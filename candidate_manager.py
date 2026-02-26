import os
import json
from datetime import datetime

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
    def __init__(self, db_path="data/candidates.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.candidates = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def _save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.candidates, f, ensure_ascii=False, indent=2)

    def add_candidate(self, name, role, hc_id="", source="", linkedin_url="", notes=""):
        """Add a new candidate. Returns the new candidate dict."""
        candidate = {
            "id": f"cand_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name,
            "role": role,
            "hc_id": hc_id,
            "source": source,
            "linkedin_url": linkedin_url,
            "stage": "Sourced",
            "score": None,
            "notes": notes,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
            "history": [{"stage": "Sourced", "date": datetime.now().strftime("%Y-%m-%d"), "note": "Added to pipeline"}],
        }
        self.candidates.append(candidate)
        self._save()
        return candidate

    def move_stage(self, candidate_id, new_stage, note=""):
        """Move a candidate to a new pipeline stage."""
        for c in self.candidates:
            if c["id"] == candidate_id:
                old_stage = c["stage"]
                c["stage"] = new_stage
                c["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                c.setdefault("history", []).append({
                    "stage": new_stage,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "note": note or f"Moved from {old_stage}",
                })
                self._save()
                return True
        return False

    def update_score(self, candidate_id, score):
        for c in self.candidates:
            if c["id"] == candidate_id:
                c["score"] = score
                c["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                self._save()
                return True
        return False

    def add_note(self, candidate_id, note):
        for c in self.candidates:
            if c["id"] == candidate_id:
                existing = c.get("notes", "")
                timestamp = datetime.now().strftime("%m-%d")
                c["notes"] = f"[{timestamp}] {note}\n{existing}".strip()
                c["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                self._save()
                return True
        return False

    def delete_candidate(self, candidate_id):
        self.candidates = [c for c in self.candidates if c["id"] != candidate_id]
        self._save()

    def get_by_stage(self, stage):
        return [c for c in self.candidates if c["stage"] == stage]

    def get_all(self):
        return sorted(self.candidates, key=lambda x: x["updated_at"], reverse=True)

    def get_stats(self):
        """Returns stage counts and total."""
        counts = {s: 0 for s in PIPELINE_STAGES}
        for c in self.candidates:
            stage = c.get("stage", "Sourced")
            if stage in counts:
                counts[stage] += 1
        return counts
