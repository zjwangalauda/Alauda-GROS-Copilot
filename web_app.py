import logging
import os

import streamlit as st
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 强制覆盖环境变量（本地开发走 .env）
load_dotenv(override=True)

# Streamlit Cloud 部署时通过 Secrets 注入 LLM 凭据（优先级高于 .env）
try:
    for key in ["OPENAI_API_KEY", "OPENAI_API_BASE", "LLM_MODEL", "STRONG_MODEL", "EMBEDDING_API_KEY", "EMBEDDING_API_BASE"]:
        val = st.secrets.get(key, "")
        if val:
            os.environ[key] = val
except Exception:
    logger.debug("No secrets.toml found — using .env for local development")

from app_shared import bi, check_password, get_agent, inject_css, _llm_cache_key  # noqa: E402

# 1. 页面级基础设置
st.set_page_config(
    page_title="Alauda GROS Copilot | Global Recruitment AI / 全球招聘智能体",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. 全局 CSS
inject_css()

# 3. 密码门控
if not check_password():
    st.stop()

# 4. 预热 Agent 缓存
get_agent(_key=_llm_cache_key())

# 5. 侧边栏 Logo
with st.sidebar:
    st.markdown(
        "<div style='text-align: center; margin-bottom: 20px;'>"
        "<img src='https://www.alauda.cn/Public/Home/images/new_header/logo_new_230524.png' width='180'>"
        "</div>",
        unsafe_allow_html=True,
    )

# 6. 页面导航
pages = {
    "Core Modules / 核心操作模块": [
        st.Page("pages/home.py",                    title="Home / 首页",                          icon="🏠", default=True),
        st.Page("pages/mod0_hc_approval.py",        title="M0: HC Approval / HC 审批",            icon="📋"),
        st.Page("pages/mod1_jd_sourcing.py",        title="M1: JD & Sourcing / JD 与寻源",        icon="🎯"),
        st.Page("pages/mod2_outreach.py",           title="M2: Outreach / 自动化触达",            icon="✉️"),
        st.Page("pages/mod3_resume_matcher.py",     title="M3: Resume Match / 简历初筛",          icon="📄"),
        st.Page("pages/mod4_scorecard.py",          title="M4: Scorecard / 面试打分卡",           icon="📝"),
        st.Page("pages/mod7_candidate_pipeline.py", title="M7: Pipeline / 候选人看板",            icon="👥"),
    ],
    "Data & Intelligence / 数据与智库": [
        st.Page("pages/dashboard.py",               title="Dashboard / 数据看板",                 icon="📊"),
        st.Page("pages/mod5_playbook_qa.py",        title="M5: Playbook Q&A / 智库问答",          icon="📚"),
        st.Page("pages/mod6_knowledge_harvester.py", title="M6: Knowledge Harvester / 知识收割",   icon="🏗️"),
    ],
}

pg = st.navigation(pages, position="sidebar")

# 7. 侧边栏底部
with st.sidebar:
    st.markdown("---")
    if st.button(bi("🔄 Clear cache (click if errors)", "🔄 强制清理缓存 (如遇异常请点击)"), use_container_width=True):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.success(bi("✅ Cache cleared", "✅ 缓存已清空"))
        st.rerun()
    st.markdown("""
    <div style="font-size: 0.85rem; color: #6B7280; line-height: 1.5; background-color: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
    💡 <b>About / 系统说明</b><br>
    Built on the Alauda Global Recruitment Operating System (GROS). AI-powered end-to-end recruitment pipeline for precision capture of elite overseas talent.<br>
    本系统基于《Alauda 全球技术精英招聘操作系统 (GROS)》构建，由 AI 赋能招聘全流程，旨在实现海外精英人才的精准流水线式捕获。
    </div>
    """, unsafe_allow_html=True)

# 8. 运行当前选中页面
pg.run()
