import os
import json
import fcntl
import uuid
from datetime import datetime

HC_VALID_STATUSES = {"Pending", "Approved", "Rejected"}

class HCManager:
    """
    HC (Headcount) 管理器，负责处理业务部门的需求申请与HR的审批逻辑。
    数据持久化保存在 data/hc_requests.json 中。
    """
    def __init__(self, db_path="data/hc_requests.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.requests = self._load_requests()

    def _load_requests(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    fcntl.flock(f, fcntl.LOCK_SH)
                    try:
                        return json.load(f)
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
            except json.JSONDecodeError:
                return []
        return []

    def _save_requests(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(self.requests, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def submit_request(self, department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point):
        """业务线提交新的 HC 需求"""
        req_id = f"HC_{uuid.uuid4().hex[:12]}"
        hc_req = {
            "id": req_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "department": department,
            "role_title": role_title,
            "location": location,
            "urgency": urgency,
            "mission": mission,
            "tech_stack": tech_stack,
            "deal_breakers": deal_breakers,
            "selling_point": selling_point,
            "status": "Pending" # 状态: Pending (待审批), Approved (已批准), Rejected (已驳回)
        }
        self.requests.append(hc_req)
        self._save_requests()
        return req_id

    def update_status(self, req_id, new_status):
        """HR 审批 HC。Returns True on success, raises ValueError on invalid status."""
        if new_status not in HC_VALID_STATUSES:
            raise ValueError(f"Invalid HC status '{new_status}'. Must be one of: {HC_VALID_STATUSES}")
        for req in self.requests:
            if req["id"] == req_id:
                req["status"] = new_status
                self._save_requests()
                return True
        return False

    def get_all_requests(self):
        return sorted(self.requests, key=lambda x: x["date"], reverse=True)

    def get_approved_requests(self):
        """获取所有已批准的 HC，供模块一生成 JD 时下拉选择"""
        return [r for r in self.requests if r["status"] == "Approved"]
