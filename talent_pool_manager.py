"""Talent Pool Manager — resume library with deduplication and AI info extraction."""

import hashlib
import logging
import os
import uuid
from datetime import date

from db import get_db

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt")


class TalentPoolManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self._ensure_table()

    def _conn(self):
        return get_db(self.db_path)

    def _ensure_table(self):
        """Table is created by db.init_db(); this is a no-op safety check."""
        pass

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_files(self, files, agent) -> dict:
        """Import uploaded file objects (Streamlit UploadedFile or similar).

        Each file must have .name (str) and .read() -> bytes.
        Returns {"imported": int, "skipped_dup": int, "skipped_unsupported": int, "errors": list[str]}.
        """
        stats = {"imported": 0, "skipped_dup": 0, "skipped_unsupported": 0, "errors": []}
        for f in files:
            name = f.name
            if not name.lower().endswith(SUPPORTED_EXTENSIONS):
                stats["skipped_unsupported"] += 1
                continue
            try:
                file_bytes = f.read()
                result = self._import_one(name, file_bytes, agent)
                if result == "dup":
                    stats["skipped_dup"] += 1
                elif result == "ok":
                    stats["imported"] += 1
                else:
                    stats["errors"].append(f"{name}: {result}")
            except Exception as e:
                stats["errors"].append(f"{name}: {e}")
        return stats

    def import_from_directory(self, dir_path: str, agent) -> dict:
        """Scan a directory for resume files and import them.

        Returns same stats dict as import_files.
        """
        stats = {"imported": 0, "skipped_dup": 0, "skipped_unsupported": 0, "errors": []}
        dir_path = os.path.expanduser(dir_path)
        if not os.path.isdir(dir_path):
            stats["errors"].append(f"Directory not found: {dir_path}")
            return stats

        for fname in sorted(os.listdir(dir_path)):
            if not fname.lower().endswith(SUPPORTED_EXTENSIONS):
                stats["skipped_unsupported"] += 1
                continue
            fpath = os.path.join(dir_path, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "rb") as fh:
                    file_bytes = fh.read()
                result = self._import_one(fname, file_bytes, agent)
                if result == "dup":
                    stats["skipped_dup"] += 1
                elif result == "ok":
                    stats["imported"] += 1
                else:
                    stats["errors"].append(f"{fname}: {result}")
            except Exception as e:
                stats["errors"].append(f"{fname}: {e}")
        return stats

    def _import_one(self, file_name: str, file_bytes: bytes, agent) -> str:
        """Import a single file. Returns 'ok', 'dup', or an error message."""
        file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
        conn = self._conn()

        # Check for duplicate
        existing = conn.execute(
            "SELECT id FROM talent_pool WHERE file_hash = ?", (file_hash,)
        ).fetchone()
        if existing:
            return "dup"

        # Parse text
        parsed_text = agent.extract_text_from_file(file_name, file_bytes)
        if parsed_text.startswith("File parsing failed") or parsed_text.startswith("Unsupported"):
            return parsed_text

        # Extract candidate info via LLM
        info = agent.extract_candidate_info(parsed_text)

        talent_id = f"tp_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """INSERT INTO talent_pool
               (id, file_name, file_hash, parsed_text, candidate_name, email, phone, linkedin_url, tags, uploaded_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                talent_id,
                file_name,
                file_hash,
                parsed_text,
                info.get("candidate_name", ""),
                info.get("email", ""),
                info.get("phone", ""),
                info.get("linkedin_url", ""),
                info.get("tags", ""),
                date.today().isoformat(),
            ),
        )
        conn.commit()
        return "ok"

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_active_talents(self, since_date: str | None = None) -> list[dict]:
        """Return active talent pool entries, optionally filtered by upload date >= since_date."""
        conn = self._conn()
        if since_date:
            rows = conn.execute(
                "SELECT * FROM talent_pool WHERE is_active = 1 AND uploaded_at >= ? ORDER BY uploaded_at DESC",
                (since_date,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM talent_pool WHERE is_active = 1 ORDER BY uploaded_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_talent(self, talent_id: str) -> dict | None:
        conn = self._conn()
        row = conn.execute("SELECT * FROM talent_pool WHERE id = ?", (talent_id,)).fetchone()
        return dict(row) if row else None

    def get_all(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM talent_pool ORDER BY uploaded_at DESC").fetchall()
        return [dict(r) for r in rows]

    def deactivate(self, talent_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("UPDATE talent_pool SET is_active = 0 WHERE id = ?", (talent_id,))
        conn.commit()
        return cur.rowcount > 0

    def reactivate(self, talent_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("UPDATE talent_pool SET is_active = 1 WHERE id = ?", (talent_id,))
        conn.commit()
        return cur.rowcount > 0

    def get_stats(self) -> dict:
        conn = self._conn()
        total = conn.execute("SELECT COUNT(*) FROM talent_pool").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM talent_pool WHERE is_active = 1").fetchone()[0]
        today = date.today().isoformat()
        # Talents uploaded in the last 7 days
        week_ago = date.today().replace(day=max(1, date.today().day - 7)).isoformat()
        recent = conn.execute(
            "SELECT COUNT(*) FROM talent_pool WHERE uploaded_at >= ?", (week_ago,)
        ).fetchone()[0]
        return {"total": total, "active": active, "recent_7d": recent}

    def get_all_with_eval_status(self) -> list[dict]:
        """Return all talents with their best evaluation score and verdict from shortlist."""
        conn = self._conn()
        rows = conn.execute(
            """SELECT t.*,
                      sl_best.best_score, sl_best.best_verdict, sl_best.eval_count
               FROM talent_pool t
               LEFT JOIN (
                   SELECT talent_id,
                          MAX(score) AS best_score,
                          -- Get verdict of highest score
                          (SELECT verdict FROM shortlist s2
                           WHERE s2.talent_id = s.talent_id
                           ORDER BY s2.score DESC LIMIT 1) AS best_verdict,
                          COUNT(*) AS eval_count
                   FROM shortlist s
                   GROUP BY talent_id
               ) sl_best ON t.id = sl_best.talent_id
               ORDER BY t.uploaded_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
