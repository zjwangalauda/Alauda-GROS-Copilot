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

from app_shared import check_password, get_agent, inject_css

# 1. 页面级基础设置
st.set_page_config(
    page_title="Alauda GROS Copilot | 全球招聘智能体",
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
get_agent()

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
    "核心操作模块": [
        st.Page("pages/home.py",                    title="首页：全流程作战大盘",         icon="🏠", default=True),
        st.Page("pages/mod0_hc_approval.py",        title="模块零：HC 业务需求审批",      icon="📋"),
        st.Page("pages/mod1_jd_sourcing.py",        title="模块一：JD 逆向与自动寻源",    icon="🎯"),
        st.Page("pages/mod2_outreach.py",           title="模块二：自动化触达",           icon="✉️"),
        st.Page("pages/mod3_resume_matcher.py",     title="模块三：简历智能初筛",         icon="📄"),
        st.Page("pages/mod4_scorecard.py",          title="模块四：结构化面试打分卡",      icon="📝"),
        st.Page("pages/mod7_candidate_pipeline.py", title="模块七：候选人 Pipeline 看板", icon="👥"),
    ],
    "数据与智库": [
        st.Page("pages/dashboard.py",               title="招聘数据看板",                 icon="📊"),
        st.Page("pages/mod5_playbook_qa.py",        title="模块五：Playbook 智库问答",    icon="📚"),
        st.Page("pages/mod6_knowledge_harvester.py", title="模块六：知识库自生长",         icon="🏗️"),
    ],
}

pg = st.navigation(pages, position="sidebar")

# 7. 侧边栏底部
with st.sidebar:
    st.markdown("---")
    if st.button("🔄 强制清理云端缓存 (如遇异常请点击)", use_container_width=True):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.success("✅ 缓存已清空")
        st.rerun()
    st.markdown("""
    <div style="font-size: 0.85rem; color: #6B7280; line-height: 1.5; background-color: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
    💡 <b>系统说明</b><br>
    本系统基于《Alauda 全球技术精英招聘操作系统 (GROS)》构建，由 AI 赋能招聘全流程，旨在实现海外精英人才的精准流水线式捕获。
    </div>
    """, unsafe_allow_html=True)

# 8. 运行当前选中页面
pg.run()
