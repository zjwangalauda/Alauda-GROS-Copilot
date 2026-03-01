"""Shared singletons, helpers, and CSS for all pages."""

import hmac
import logging
import os
import json

import streamlit as st

from db import get_db

logger = logging.getLogger(__name__)

# Ensure SQLite tables exist on import
get_db()


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------
def inject_css():
    """Inject the global CSS theme — call once from the entrypoint."""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "theme.css")
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Auth gate
# ---------------------------------------------------------------------------
def check_password() -> bool:
    """Returns True if user is authenticated, False otherwise."""
    _pwd = ""
    try:
        _pwd = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        logger.debug("Could not read APP_PASSWORD from secrets, falling back to env")
    if not _pwd:
        _pwd = os.environ.get("APP_PASSWORD", "")
    # No password configured → open access (dev mode)
    if not _pwd:
        return True
    if st.session_state.get("_authenticated"):
        return True
    with st.container():
        st.markdown(
            "<div style='max-width:400px;margin:80px auto;background:#fff;border:1px solid #E2E8F0;"
            "border-radius:12px;padding:40px;box-shadow:0 4px 16px rgba(0,0,0,0.08);'>"
            "<div style='text-align:center;margin-bottom:24px;'>"
            "<img src='https://www.alauda.cn/Public/Home/images/new_header/logo_new_230524.png' width='160'>"
            "<h2 style='color:#004D99;margin-top:16px;font-size:1.2rem;'>GROS Copilot — 访问验证</h2>"
            "<p style='color:#64748B;font-size:0.9rem;'>请输入访问密码以继续</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        _input = st.text_input("访问密码", type="password", key="_login_input", label_visibility="collapsed", placeholder="请输入访问密码...")
        if st.button("登录", type="primary", use_container_width=True):
            if hmac.compare_digest(_input, _pwd):
                st.session_state["_authenticated"] = True
                st.rerun()
            else:
                st.error("密码错误，请重试。")
    return False


# ---------------------------------------------------------------------------
# Cached singletons
# ---------------------------------------------------------------------------
def _llm_cache_key():
    """Return a tuple of LLM credentials so the cache auto-invalidates when secrets change."""
    return (
        os.environ.get("OPENAI_API_KEY", ""),
        os.environ.get("OPENAI_API_BASE", ""),
        os.environ.get("LLM_MODEL", ""),
        os.environ.get("STRONG_MODEL", ""),
    )


def _emb_cache_key():
    """Return a tuple of embedding credentials so the cache auto-invalidates when secrets change."""
    return (
        os.environ.get("EMBEDDING_API_KEY", ""),
        os.environ.get("EMBEDDING_API_BASE", ""),
    )


@st.cache_resource
def get_agent(_key=None):
    from recruitment_agent import RecruitmentAgent
    return RecruitmentAgent()


@st.cache_resource
def get_rag_system(_key=None):
    from document_parser import RAGSystem
    return RAGSystem()


# ---------------------------------------------------------------------------
# Shared helper: load latest JD
# ---------------------------------------------------------------------------
def load_latest_jd():
    """Return (jd_text, info_message) from session_state or disk.

    Returns ("", warning_message) when nothing is available.
    """
    if "generated_jd" in st.session_state:
        return st.session_state["generated_jd"], "💡 Auto-loaded from Module 1."
    if os.path.exists("data/generated/latest_jd.json"):
        with open("data/generated/latest_jd.json", encoding="utf-8") as f:
            rec = json.load(f)
        jd_text = rec["jd_content"]
        st.session_state["generated_jd"] = jd_text
        return jd_text, f"💡 Auto-restored last generated JD ({rec['role_title']} · {rec['generated_at'][:10]})"
    return "", ""
