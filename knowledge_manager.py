import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta

from db import get_db


class KnowledgeManager:
    """
    负责管理从 0 到 1 积累的"招聘经验碎片"，
    最终可输出为 Markdown 并送入 RAG 向量库。
    """
    def __init__(self, db_path: str | None = None):
        self._migrate_json(db_path)

    def _migrate_json(self, legacy_path: str | None) -> None:
        """One-time migration: import legacy JSON into SQLite if it exists."""
        path = legacy_path or os.path.join("data", "playbook_fragments.json")
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
        existing = conn.execute("SELECT COUNT(*) FROM playbook_fragments").fetchone()[0]
        if existing > 0:
            return
        for frag in records:
            tags = ",".join(frag.get("tags", []))
            conn.execute(
                "INSERT OR IGNORE INTO playbook_fragments (id, date, expires_at, content_hash, source_url, region, category, content, tags) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (frag["id"], frag.get("date"), frag.get("expires_at"),
                 frag.get("content_hash"), frag.get("source_url", ""),
                 frag.get("region"), frag.get("category"), frag.get("content"), tags),
            )
        conn.commit()

    def add_fragment(self, region: str, category: str, content: str,
                     tags: str = "", source_url: str = "", ttl_days: int = 90) -> tuple[bool, str]:
        """Add a knowledge fragment. Returns (True, 'added') or (False, 'duplicate')."""
        content_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:12]
        conn = get_db()
        dup = conn.execute("SELECT id FROM playbook_fragments WHERE content_hash = ?", (content_hash,)).fetchone()
        if dup:
            return False, "duplicate"
        frag_id = f"frag_{uuid.uuid4().hex[:12]}"
        date = datetime.now().strftime("%Y-%m-%d")
        expires_at = (datetime.now() + timedelta(days=ttl_days)).strftime("%Y-%m-%d")
        tag_str = ",".join(t.strip() for t in tags.split(",")) if tags else ""
        conn.execute(
            "INSERT INTO playbook_fragments (id, date, expires_at, content_hash, source_url, region, category, content, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (frag_id, date, expires_at, content_hash, source_url, region, category, content, tag_str),
        )
        conn.commit()
        return True, "added"

    def get_expiry_status(self, fragment: dict) -> str:
        """Returns 'expired', 'expiring_soon' (<=14 days), or 'ok'."""
        expires_at = fragment.get("expires_at")
        if not expires_at:
            return "ok"
        try:
            exp_date = datetime.strptime(expires_at, "%Y-%m-%d")
            days_left = (exp_date - datetime.now()).days
            if days_left < 0:
                return "expired"
            if days_left <= 14:
                return "expiring_soon"
            return "ok"
        except ValueError:
            return "ok"

    def get_all_fragments(self) -> list[dict]:
        conn = get_db()
        rows = conn.execute("SELECT * FROM playbook_fragments ORDER BY date DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tags"] = [t for t in (d.get("tags") or "").split(",") if t]
            result.append(d)
        return result

    def compile_to_markdown(self, output_file: str = "data/Alauda_Dynamic_Playbook.md") -> bool:
        """将所有碎片编译合成一个完整的 Markdown 知识库文件，供 RAG 使用"""
        fragments = self.get_all_fragments()
        if not fragments:
            return False

        md_content = "# Alauda 动态演进招聘知识库 (Dynamic Playbook)\n\n"
        md_content += f"*上次更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        md_content += "---\n\n"

        regions = set(f["region"] for f in fragments)
        for region in regions:
            md_content += f"## 🌍 区域: {region}\n\n"
            region_frags = [f for f in fragments if f["region"] == region]

            categories = set(f["category"] for f in region_frags)
            for category in categories:
                md_content += f"### 📌 {category}\n\n"
                cat_frags = [f for f in region_frags if f["category"] == category]

                for idx, frag in enumerate(cat_frags, 1):
                    status = self.get_expiry_status(frag)
                    expired_mark = " ⚠️ [EXPIRED — may be outdated]" if status == "expired" else ""
                    md_content += f"**经验规则 {idx} ({frag['date']}){expired_mark}**\n"
                    md_content += f"> {frag['content']}\n\n"
                    if frag.get("expires_at"):
                        md_content += f"*有效期至: {frag['expires_at']}*\n\n"
                    if frag.get("tags"):
                        md_content += f"*标签: {', '.join(frag['tags'])}*\n\n"
                    if frag.get("source_url"):
                        md_content += f"*来源: {frag['source_url']}*\n\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        return True
