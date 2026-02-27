import os
import json
import fcntl
import hashlib
import uuid
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

class KnowledgeManager:
    """
    负责管理从 0 到 1 积累的“招聘经验碎片”，
    最终可输出为 Markdown 并送入 RAG 向量库。
    """
    def __init__(self, db_path="data/playbook_fragments.json"):
        self.db_path = db_path
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.fragments = self._load_fragments()

    def _load_fragments(self):
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

    def _save_fragments(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(self.fragments, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def add_fragment(self, region, category, content, tags="", source_url="", ttl_days=90):
        """Add a knowledge fragment. Returns (True, 'added') or (False, 'duplicate')."""
        content_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:12]
        for existing in self.fragments:
            if existing.get("content_hash") == content_hash:
                return False, "duplicate"
        expires_at = (datetime.now() + timedelta(days=ttl_days)).strftime("%Y-%m-%d")
        fragment = {
            "id": f"frag_{uuid.uuid4().hex[:12]}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "expires_at": expires_at,
            "content_hash": content_hash,
            "source_url": source_url,
            "region": region,
            "category": category,
            "content": content,
            "tags": [t.strip() for t in tags.split(",")] if tags else []
        }
        self.fragments.append(fragment)
        self._save_fragments()
        return True, "added"

    def get_expiry_status(self, fragment):
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

    def get_all_fragments(self):
        return sorted(self.fragments, key=lambda x: x["date"], reverse=True)

    def compile_to_markdown(self, output_file="data/Alauda_Dynamic_Playbook.md"):
        """将所有碎片编译合成一个完整的 Markdown 知识库文件，供 RAG 使用"""
        if not self.fragments:
            return False
            
        md_content = "# Alauda 动态演进招聘知识库 (Dynamic Playbook)\n\n"
        md_content += f"*上次更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        md_content += "---\n\n"
        
        # 按地区分组
        regions = set(f["region"] for f in self.fragments)
        for region in regions:
            md_content += f"## 🌍 区域: {region}\n\n"
            region_frags = [f for f in self.fragments if f["region"] == region]
            
            # 按分类细化
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
