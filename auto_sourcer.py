"""Auto Sourcer — automated talent matching engine.

Scans the talent pool against all approved HCs, scores candidates using the M3
evaluation rubric, and produces shortlists. Supports full and incremental runs.
"""

import logging
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

from db import get_db
from hc_manager import HCManager
from talent_pool_manager import TalentPoolManager
from candidate_manager import CandidateManager

logger = logging.getLogger(__name__)

# Candidates marked "Not Interested" are frozen for this many days
FREEZE_DAYS = 180
# Only shortlist candidates scoring at or above this threshold
PASS_THRESHOLD = 60
# Max parallel LLM evaluation workers
MAX_WORKERS = 5


class AutoSourcer:
    def __init__(self, agent, db_path: str | None = None):
        self.agent = agent
        self.db_path = db_path
        self.hm = HCManager(db_path)
        self.tpm = TalentPoolManager(db_path)
        self.cm = CandidateManager(db_path)

    def _conn(self):
        return get_db(self.db_path)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, force_full: bool = False) -> str:
        """Execute an auto-sourcing run. Returns the run_id."""
        conn = self._conn()
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        is_incremental = (not force_full) and self._has_previous_run()
        run_type = "incremental" if is_incremental else "full"
        start = time.time()

        conn.execute(
            """INSERT INTO sourcing_runs (id, run_date, run_type, hc_count, talent_scanned, matches_found, status)
               VALUES (?, ?, ?, 0, 0, 0, 'running')""",
            (run_id, datetime.now().strftime("%Y-%m-%d %H:%M"), run_type),
        )
        conn.commit()

        try:
            approved_hcs = self.hm.get_approved_requests()
            if not approved_hcs:
                self._finish_run(run_id, 0, 0, 0, time.time() - start, "completed")
                return run_id

            talents = self._get_talent_pool(is_incremental)
            if not talents:
                self._finish_run(run_id, len(approved_hcs), 0, 0, time.time() - start, "completed")
                return run_id

            total_matches = 0
            total_scanned = 0

            for hc in approved_hcs:
                jd_text = self._build_jd_from_hc(hc)
                # Filter out frozen/already-decided talents for this HC
                eligible = [t for t in talents if not self._should_skip(t["id"], hc["id"])]
                total_scanned += len(eligible)

                if not eligible:
                    continue

                # Parallel evaluation
                results = {}
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {
                        executor.submit(self._evaluate_match, jd_text, t): t
                        for t in eligible
                    }
                    for future in as_completed(futures):
                        talent = futures[future]
                        try:
                            score, verdict, eval_md = future.result()
                            results[talent["id"]] = (score, verdict, eval_md)
                        except Exception as e:
                            logger.error("Eval failed for talent %s: %s", talent["id"], e)

                # Save all evaluated results (both qualified and disqualified)
                for talent_id, (score, verdict, eval_md) in results.items():
                    self._save_result(run_id, hc["id"], talent_id, score, verdict, eval_md)
                    if score >= PASS_THRESHOLD:
                        total_matches += 1

            duration = time.time() - start
            self._finish_run(run_id, len(approved_hcs), total_scanned, total_matches, duration, "completed")

        except Exception as e:
            logger.error("Auto sourcing run failed: %s", e, exc_info=True)
            self._finish_run(run_id, 0, 0, 0, time.time() - start, "failed")
            raise

        return run_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _has_previous_run(self) -> bool:
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) FROM sourcing_runs WHERE status = 'completed'"
        ).fetchone()
        return row[0] > 0

    def _get_last_run_date(self) -> str | None:
        conn = self._conn()
        row = conn.execute(
            "SELECT run_date FROM sourcing_runs WHERE status = 'completed' ORDER BY run_date DESC LIMIT 1"
        ).fetchone()
        if row:
            # run_date is "YYYY-MM-DD HH:MM", extract date part
            return row[0][:10]
        return None

    def _get_talent_pool(self, is_incremental: bool) -> list[dict]:
        if is_incremental:
            since = self._get_last_run_date()
            if since:
                return self.tpm.get_all_talents(since_date=since)
        return self.tpm.get_all_talents()

    def _should_skip(self, talent_id: str, hc_id: str) -> bool:
        """Skip if already decided (Interested/frozen Not Interested) for this HC."""
        conn = self._conn()
        row = conn.execute(
            "SELECT disposition, disposition_date FROM shortlist WHERE talent_id = ? AND hc_id = ?",
            (talent_id, hc_id),
        ).fetchone()
        if not row:
            return False

        disposition = row[0]
        if disposition == "Interested":
            return True  # Already converted to pipeline
        if disposition == "Not Interested":
            # Check freeze window
            disp_date = row[1]
            if disp_date:
                try:
                    frozen_until = datetime.strptime(disp_date, "%Y-%m-%d") + timedelta(days=FREEZE_DAYS)
                    if datetime.now() < frozen_until:
                        return True  # Still frozen
                except ValueError:
                    pass
            return False  # Freeze expired, re-evaluate
        # disposition == "Pending" — re-evaluate with new run
        return False

    def _build_jd_from_hc(self, hc: dict) -> str:
        """Build a structured JD text from HC fields for M3 scoring."""
        return f"""## Job Description — {hc.get('role_title', 'N/A')}

**Location:** {hc.get('location', 'N/A')}
**Department:** {hc.get('department', 'N/A')}

### Year-1 Mission
{hc.get('mission', 'N/A')}

### Required Tech Stack
{hc.get('tech_stack', 'N/A')}

### Deal Breakers (Hard Disqualifiers)
{hc.get('deal_breakers', 'N/A')}

### Why Join Alauda
{hc.get('selling_point', 'N/A')}
"""

    def _evaluate_match(self, jd_text: str, talent: dict) -> tuple[float, str, str]:
        """Evaluate a talent against a JD. Returns (score, verdict, evaluation_markdown)."""
        eval_md = self.agent.evaluate_resume(jd_text, talent["parsed_text"])
        score, verdict = self._parse_score(eval_md)
        return score, verdict, eval_md

    def _parse_score(self, evaluation_md: str) -> tuple[float, str]:
        """Extract numeric score and verdict from M3 evaluation markdown."""
        score = 0.0
        verdict = "Disqualified"

        # Match "Total Score: XX / 100" or "**Total Score**: XX / 100"
        score_match = re.search(r"Total Score[*]*:\s*(\d+(?:\.\d+)?)\s*/\s*100", evaluation_md)
        if score_match:
            score = float(score_match.group(1))

        # Match verdict
        verdict_match = re.search(r"Verdict[*]*:\s*(Strong Match|Borderline Pass|Disqualified)", evaluation_md)
        if verdict_match:
            verdict = verdict_match.group(1)
        elif score >= 80:
            verdict = "Strong Match"
        elif score >= 60:
            verdict = "Borderline Pass"

        return score, verdict

    def _save_result(self, run_id: str, hc_id: str, talent_id: str,
                     score: float, verdict: str, eval_md: str) -> None:
        """UPSERT shortlist entry — update score if HC+talent combo exists."""
        conn = self._conn()
        sl_id = f"sl_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """INSERT INTO shortlist (id, run_id, hc_id, talent_id, score, verdict, evaluation_md, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(hc_id, talent_id) DO UPDATE SET
                   run_id = excluded.run_id,
                   score = excluded.score,
                   verdict = excluded.verdict,
                   evaluation_md = excluded.evaluation_md,
                   created_at = excluded.created_at
                   WHERE shortlist.disposition = 'Pending'""",
            (sl_id, run_id, hc_id, talent_id, score, verdict, eval_md, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()

    def _finish_run(self, run_id: str, hc_count: int, scanned: int,
                    matches: int, duration: float, status: str) -> None:
        conn = self._conn()
        conn.execute(
            """UPDATE sourcing_runs SET hc_count=?, talent_scanned=?, matches_found=?,
               duration_seconds=?, status=? WHERE id=?""",
            (hc_count, scanned, matches, round(duration, 1), status, run_id),
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Query & Disposition
    # ------------------------------------------------------------------

    def get_run_history(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM sourcing_runs ORDER BY run_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_shortlist(self, hc_id: str | None = None, run_id: str | None = None,
                      disposition: str | None = None, qualified: str | None = None) -> list[dict]:
        """Query shortlist with optional filters. Joins talent_pool for candidate info.

        qualified: "qualified" (score >= PASS_THRESHOLD), "disqualified" (< PASS_THRESHOLD), or None (all).
        """
        conn = self._conn()
        sql = """
            SELECT s.*, t.candidate_name, t.file_name, t.email, t.phone,
                   t.linkedin_url AS talent_linkedin, t.tags AS talent_tags,
                   h.role_title, h.location AS hc_location, h.department
            FROM shortlist s
            JOIN talent_pool t ON s.talent_id = t.id
            JOIN hc_requests h ON s.hc_id = h.id
            WHERE 1=1
        """
        params = []
        if hc_id:
            sql += " AND s.hc_id = ?"
            params.append(hc_id)
        if run_id:
            sql += " AND s.run_id = ?"
            params.append(run_id)
        if disposition:
            sql += " AND s.disposition = ?"
            params.append(disposition)
        if qualified == "qualified":
            sql += " AND s.score >= ?"
            params.append(PASS_THRESHOLD)
        elif qualified == "disqualified":
            sql += " AND s.score < ?"
            params.append(PASS_THRESHOLD)
        sql += " ORDER BY s.score DESC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_frozen_list(self) -> list[dict]:
        """Get all 'Not Interested' entries still within freeze window."""
        conn = self._conn()
        cutoff = (datetime.now() - timedelta(days=FREEZE_DAYS)).strftime("%Y-%m-%d")
        rows = conn.execute(
            """SELECT s.*, t.candidate_name, t.file_name, t.email,
                      h.role_title, h.location AS hc_location
               FROM shortlist s
               JOIN talent_pool t ON s.talent_id = t.id
               JOIN hc_requests h ON s.hc_id = h.id
               WHERE s.disposition = 'Not Interested'
                 AND s.disposition_date >= ?
               ORDER BY s.disposition_date DESC""",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def set_disposition(self, shortlist_id: str, disposition: str, note: str = "") -> bool:
        """Set disposition on a shortlist entry. disposition: 'Interested' | 'Not Interested'."""
        if disposition not in ("Interested", "Not Interested"):
            raise ValueError(f"Invalid disposition: {disposition}")
        conn = self._conn()
        cur = conn.execute(
            """UPDATE shortlist SET disposition=?, disposition_note=?, disposition_date=?
               WHERE id=?""",
            (disposition, note, date.today().isoformat(), shortlist_id),
        )
        conn.commit()
        return cur.rowcount > 0

    def convert_to_candidate(self, shortlist_id: str) -> str | None:
        """Convert a shortlist entry to a candidate in the main pipeline.

        Sets stage to 'Contacted', source to 'Auto Sourcing', and links back.
        Returns the new candidate_id or None on failure.
        """
        conn = self._conn()
        row = conn.execute(
            """SELECT s.*, t.candidate_name, t.linkedin_url, t.email
               FROM shortlist s
               JOIN talent_pool t ON s.talent_id = t.id
               WHERE s.id = ?""",
            (shortlist_id,),
        ).fetchone()
        if not row:
            return None

        sl = dict(row)
        # Get HC info for role
        hc = conn.execute("SELECT role_title FROM hc_requests WHERE id = ?", (sl["hc_id"],)).fetchone()
        role = hc["role_title"] if hc else "Unknown"

        candidate = self.cm.add_candidate(
            name=sl["candidate_name"] or "Unknown",
            role=role,
            hc_id=sl["hc_id"],
            source="Auto Sourcing",
            linkedin_url=sl.get("linkedin_url") or sl.get("talent_linkedin") or "",
            notes=f"Auto-sourced. Score: {sl['score']}/100 ({sl['verdict']}). Contact: {sl.get('email', '')}",
        )

        # Update score
        self.cm.update_score(candidate["id"], sl["score"])
        # Move to Contacted stage
        self.cm.move_stage(candidate["id"], "Contacted", note="Auto-sourced and marked as interested by HR")

        # Link back
        conn.execute(
            "UPDATE shortlist SET disposition='Interested', disposition_date=?, candidate_id=? WHERE id=?",
            (date.today().isoformat(), candidate["id"], shortlist_id),
        )
        conn.commit()

        return candidate["id"]

    def unfreeze(self, shortlist_id: str) -> bool:
        """Manually unfreeze a 'Not Interested' entry by resetting to Pending."""
        conn = self._conn()
        cur = conn.execute(
            """UPDATE shortlist SET disposition='Pending', disposition_note='', disposition_date=NULL
               WHERE id=? AND disposition='Not Interested'""",
            (shortlist_id,),
        )
        conn.commit()
        return cur.rowcount > 0
