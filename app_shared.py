"""Shared singletons, helpers, and CSS for all pages."""

import logging
import os
import json

import streamlit as st

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------
def inject_css():
    """Inject the global CSS theme — call once from the entrypoint."""
    st.markdown("""
<style>
    :root {
        --alauda-blue: #004D99;
        --alauda-light-blue: #E6F0FA;
        --bg-color: #F8FAFC;
        --card-bg: #FFFFFF;
        --sidebar-bg: #FFFFFF;
        --text-main: #111827;
        --text-sub: #4B5563;
        --border-color: #E2E8F0;
    }

    .stApp {
        background-color: var(--bg-color);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }

    p, h1, h2, h3, h4, h5, h6, li, label, .stMarkdown {
        color: var(--text-main) !important;
    }

    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {
        background-color: rgba(248, 250, 252, 0.95) !important;
        border-bottom: 1px solid var(--border-color) !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
        padding-top: 2rem;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--text-sub) !important;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--alauda-blue) !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .sub-title {
        font-size: 1.1rem;
        color: var(--text-sub) !important;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }


    /* 解决下拉框和其弹出列表黑底黑字的问题 */

    /* 解决下拉框选中后的显示文本 */
    div[data-baseweb="select"] div {
        color: #111827 !important;
    }

    div[data-baseweb="select"] span {
        color: #111827 !important;
    }

    /* 极广域覆盖所有 Streamlit 弹出菜单底色 */
    div[role="listbox"],
    div[data-testid="stSelectbox"] ul,
    ul[data-baseweb="menu"],
    [data-baseweb="popover"],
    div[id*="popover"] {
        background-color: #FFFFFF !important;
    }

    /* 覆盖列表选项内容 */
    li[role="option"],
    div[role="option"],
    [data-baseweb="menu-item"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }

    /* Hover 状态覆盖 */
    li[role="option"]:hover,
    div[role="option"]:hover,
    [data-baseweb="menu-item"]:hover {
        background-color: #F3F4F6 !important;
        color: #004D99 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
    }

    /* 下拉选项弹窗区域的白底黑字 */
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }

    /* 列表中的每一个选项 */
    li[data-baseweb="menu-item"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }

    /* 鼠标悬停（Hover）在某个选项上时的浅蓝色高亮 */
    li[data-baseweb="menu-item"]:hover,
    li[data-baseweb="menu-item"][aria-selected="true"] {
        background-color: #F3F4F6 !important;
        color: #004D99 !important;
        font-weight: 500;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--alauda-blue) !important;
        box-shadow: 0 0 0 1px var(--alauda-blue) !important;
    }

    .stButton > button {
        background-color: var(--card-bg);
        color: var(--text-main);
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stButton > button:hover {
        background-color: #F9FAFB;
        border-color: #9CA3AF;
        color: var(--text-main);
    }

    .stButton > button[kind="primary"] {
        background-color: var(--alauda-blue);
        color: #FFFFFF !important;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #003366;
    }

    code, pre {
        background-color: #F3F4F6 !important;
        color: #111827 !important;
        border-radius: 4px;
        border: 1px solid #E5E7EB;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.5rem 0;
        font-size: 0.95rem;
        background-color: #FFFFFF;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background-color: var(--alauda-light-blue);
        color: var(--alauda-blue) !important;
        font-weight: 600;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 2px solid var(--alauda-blue);
    }
    td {
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
        color: var(--text-main) !important;
    }
    tr:nth-child(even) {
        background-color: #F9FAFB;
    }

    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    [data-testid="stChatMessage"] .stMarkdown p {
        color: #111827 !important;
    }
</style>
""", unsafe_allow_html=True)


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
            if _input == _pwd:
                st.session_state["_authenticated"] = True
                st.rerun()
            else:
                st.error("密码错误，请重试。")
    return False


# ---------------------------------------------------------------------------
# Cached singletons
# ---------------------------------------------------------------------------
@st.cache_resource
def get_agent():
    from recruitment_agent import RecruitmentAgent
    return RecruitmentAgent()


@st.cache_resource
def get_rag_system():
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
