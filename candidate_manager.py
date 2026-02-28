import json
import os
import uuid
from datetime import datetime

from db import get_db

PIPELINE_STAGES = [
    "Sourced",
    "Contacted",
    "Phone Screen",
    "Interview",
    "Offer",
    "Hired",
    "Rejected",
]

STAGE_COLORS = {
    "Sourced":      "#64748B",
    "Contacted":    "#3B82F6",
    "Phone Screen": "#8B5CF6",
    "Interview":    "#F59E0B",
    "Offer":        "#10B981",
    "Hired":        "#059669",
    "Rejected":     "#DC2626",
}


class CandidateManager:
    def __init__(self, db_path: str | None = None):
        self._migrate_json(db_path)

    def _migrate_json(self, legacy_path: str | None) -> None:
        """One-time migration: import legacy JSON into SQLite if it exists."""
        path = legacy_path or os.path.join("data", "candidates.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not records:
            return
        conn = get_db()
        existing = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        if existing > 0:
            return
        for c in records:
            conn.execute(
                "INSERT OR IGNORE INTO candidates (id, name, role, hc_id, source, linkedin_url, stage, score, notes, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (c["id"], c.get("name"), c.get("role"), c.get("hc_id", ""),
                 c.get("source", ""), c.get("linkedin_url", ""), c.get("stage", "Sourced"),
                 c.get("score"), c.get("notes", ""),
                 c.get("created_at"), c.get("updated_at")),
            )
            for h in c.get("history", []):
                conn.execute(
                    "INSERT INTO candidate_history (candidate_id, stage, note, date) VALUES (?, ?, ?, ?)",
                    (c["id"], h.get("stage"), h.get("note", ""), h.get("date")),
                )
        conn.commit()

    def add_candidate(self, name: str, role: str, hc_id: str = "", source: str = "",
                      linkedin_url: str = "", notes: str = "") -> dict:
        """Add a new candidate. Returns the new candidate dict."""
        cid = f"cand_{uuid.uuid4().hex[:12]}"
        now = datetime.now().strftime("%Y-%m-%d")
        conn = get_db()
        conn.execute(
            "INSERT INTO candidates (id, name, role, hc_id, source, linkedin_url, stage, score, notes, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'Sourced', NULL, ?, ?, ?)",
            (cid, name, role, hc_id, source, linkedin_url, notes, now, now),
        )
        conn.execute(
            "INSERT INTO candidate_history (candidate_id, stage, note, date) VALUES (?, 'Sourced', 'Added to pipeline', ?)",
            (cid, now),
        )
        conn.commit()
        return {
            "id": cid, "name": name, "role": role, "hc_id": hc_id,
            "source": source, "linkedin_url": linkedin_url, "stage": "Sourced",
            "score": None, "notes": notes, "created_at": now, "updated_at": now,
            "history": [{"stage": "Sourced", "date": now, "note": "Added to pipeline"}],
        }

    def move_stage(self, candidate_id: str, new_stage: str, note: str = "") -> bool:
        """Move a candidate to a new pipeline stage."""
        if new_stage not in PIPELINE_STAGES:
            raise ValueError(f"Invalid pipeline stage '{new_stage}'. Must be one of: {PIPELINE_STAGES}")
        conn = get_db()
        row = conn.execute("SELECT stage FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if row is None:
            return False
        old_stage = row["stage"]
        old_idx = PIPELINE_STAGES.index(old_stage)
        new_idx = PIPELINE_STAGES.index(new_stage)
        is_backward = new_idx < old_idx and new_stage != "Rejected"
        is_leaving_rejected = old_stage == "Rejected" and new_stage != "Rejected"
        if (is_backward or is_leaving_rejected) and not note.strip():
            raise ValueError(
                f"A note is required when moving backward (from '{old_stage}' to '{new_stage}')."
            )
        now = datetime.now().strftime("%Y-%m-%d")
        history_note = note or f"Moved from {old_stage}"
        conn.execute("UPDATE candidates SET stage = ?, updated_at = ? WHERE id = ?", (new_stage, now, candidate_id))
        conn.execute(
            "INSERT INTO candidate_history (candidate_id, stage, note, date) VALUES (?, ?, ?, ?)",
            (candidate_id, new_stage, history_note, now),
        )
        conn.commit()
        return True

    def update_score(self, candidate_id: str, score: float) -> bool:
        conn = get_db()
        now = datetime.now().strftime("%Y-%m-%d")
        cur = conn.execute("UPDATE candidates SET score = ?, updated_at = ? WHERE id = ?", (score, now, candidate_id))
        conn.commit()
        return cur.rowcount > 0

    def add_note(self, candidate_id: str, note: str) -> bool:
        conn = get_db()
        row = conn.execute("SELECT notes FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if row is None:
            return False
        existing = row["notes"] or ""
        timestamp = datetime.now().strftime("%m-%d")
        new_notes = f"[{timestamp}] {note}\n{existing}".strip()
        now = datetime.now().strftime("%Y-%m-%d")
        conn.execute("UPDATE candidates SET notes = ?, updated_at = ? WHERE id = ?", (new_notes, now, candidate_id))
        conn.commit()
        return True

    def delete_candidate(self, candidate_id: str) -> None:
        conn = get_db()
        conn.execute("DELETE FROM candidate_history WHERE candidate_id = ?", (candidate_id,))
        conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
        conn.commit()

    def get_by_stage(self, stage: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM candidates WHERE stage = ?", (stage,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_all(self) -> list[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM candidates ORDER BY updated_at DESC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_stats(self) -> dict[str, int]:
        """Returns stage counts and total."""
        counts = {s: 0 for s in PIPELINE_STAGES}
        conn = get_db()
        rows = conn.execute("SELECT stage, COUNT(*) as cnt FROM candidates GROUP BY stage").fetchall()
        for r in rows:
            if r["stage"] in counts:
                counts[r["stage"]] = r["cnt"]
        return counts

    def _row_to_dict(self, row) -> dict:
        """Convert a candidate row + its history into a dict matching the old JSON shape."""
        d = dict(row)
        conn = get_db()
        hist_rows = conn.execute(
            "SELECT stage, note, date FROM candidate_history WHERE candidate_id = ? ORDER BY id",
            (d["id"],),
        ).fetchall()
        d["history"] = [dict(h) for h in hist_rows]
        return d
