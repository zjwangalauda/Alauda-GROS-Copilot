import json
import os
import uuid
from datetime import datetime

from db import get_db

HC_VALID_STATUSES = {"Pending", "Approved", "Rejected"}

HC_TRANSITIONS = {
    "Pending":  {"Approved", "Rejected"},
    "Approved": set(),   # terminal
    "Rejected": set(),   # terminal
}


class HCManager:
    """
    HC (Headcount) 管理器，负责处理业务部门的需求申请与HR的审批逻辑。
    数据持久化保存在 SQLite 数据库中。
    """
    def __init__(self, db_path: str | None = None):
        # db_path kept for backward compat (ignored — singleton DB)
        self._migrate_json(db_path)

    def _migrate_json(self, legacy_path: str | None) -> None:
        """One-time migration: import legacy JSON into SQLite if it exists."""
        path = legacy_path or os.path.join("data", "hc_requests.json")
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
        existing = conn.execute("SELECT COUNT(*) FROM hc_requests").fetchone()[0]
        if existing > 0:
            return  # already migrated
        for r in records:
            conn.execute(
                "INSERT OR IGNORE INTO hc_requests (id, date, department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r["id"], r.get("date"), r.get("department"), r.get("role_title"),
                 r.get("location"), r.get("urgency"), r.get("mission"),
                 r.get("tech_stack"), r.get("deal_breakers"), r.get("selling_point"),
                 r.get("status", "Pending")),
            )
        conn.commit()

    def submit_request(self, department: str, role_title: str, location: str, urgency: str,
                       mission: str, tech_stack: str, deal_breakers: str, selling_point: str) -> str:
        """业务线提交新的 HC 需求"""
        req_id = f"HC_{uuid.uuid4().hex[:12]}"
        date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db()
        conn.execute(
            "INSERT INTO hc_requests (id, date, department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (req_id, date, department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point, "Pending"),
        )
        conn.commit()
        return req_id

    def update_status(self, req_id: str, new_status: str) -> bool:
        """HR 审批 HC。Returns True on success, raises ValueError on invalid status/transition."""
        if new_status not in HC_VALID_STATUSES:
            raise ValueError(f"Invalid HC status '{new_status}'. Must be one of: {HC_VALID_STATUSES}")
        conn = get_db()
        row = conn.execute("SELECT status FROM hc_requests WHERE id = ?", (req_id,)).fetchone()
        if row is None:
            return False
        current = row["status"]
        allowed = HC_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition HC from '{current}' to '{new_status}'. "
                f"Allowed transitions: {allowed or 'none (terminal state)'}"
            )
        conn.execute("UPDATE hc_requests SET status = ? WHERE id = ?", (new_status, req_id))
        conn.commit()
        return True

    def get_all_requests(self) -> list[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM hc_requests ORDER BY date DESC").fetchall()
        return [dict(r) for r in rows]

    def get_approved_requests(self) -> list[dict]:
        """获取所有已批准的 HC，供模块一生成 JD 时下拉选择"""
        conn = get_db()
        rows = conn.execute("SELECT * FROM hc_requests WHERE status = 'Approved' ORDER BY date DESC").fetchall()
        return [dict(r) for r in rows]
