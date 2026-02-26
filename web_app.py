import streamlit as st
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import pandas as pd

# 强制覆盖环境变量（本地开发走 .env）
load_dotenv(override=True)

# Streamlit Cloud 部署时通过 Secrets 注入 LLM 凭据（优先级高于 .env）
try:
    for key in ["OPENAI_API_KEY", "OPENAI_API_BASE", "LLM_MODEL"]:
        val = st.secrets.get(key, "")
        if val:
            os.environ[key] = val
except Exception:
    pass  # 本地开发没有 secrets.toml 时静默跳过

from recruitment_agent import RecruitmentAgent
from knowledge_manager import KnowledgeManager
from hc_manager import HCManager

# 1. 页面级基础设置 (支持浅色模式，并且占满全宽)
st.set_page_config(
    page_title="Alauda GROS Copilot | 全球招聘智能体",
    page_icon="assets/favicon.ico",
    layout="wide", # 宽屏模式，利用两侧空白
    initial_sidebar_state="expanded"
)

# 2. 注入深度定制的 CSS
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

# 3. 初始化 Agent
@st.cache_resource
def get_agent():
    return RecruitmentAgent()

agent = get_agent()

# ==========================================
# 侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown(
        f"<div style='text-align: center; margin-bottom: 20px;'><img src='https://www.alauda.cn/Public/Home/images/new_header/logo_new_230524.png' width='180'></div>", 
        unsafe_allow_html=True
    )
    
    st.markdown("### 🛠️ 核心操作模块")
    
    page = st.radio(
        "选择要执行的任务：",
        [
            "🏠 首页：全流程作战大盘", 
            "📋 模块零：HC 业务需求审批",
            "🎯 模块一：JD 逆向与自动寻源", 
            "✉️ 模块二：自动化触达 (Outreach)",
            "📄 模块三：简历智能初筛 (Resume Matcher)",
            "📝 模块四：结构化面试打分卡",
            "📚 模块五：Playbook 智库问答",
            "🏗️ 模块六：知识库自生长 (0-to-1)"
        ],
        label_visibility="collapsed"
    )

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

# ==========================================
# 主页面路由逻辑
# ==========================================

if page == "🏠 首页：全流程作战大盘":
    st.markdown('<div class="main-title">🌍 灵雀云全球精英招聘指挥中心</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">可复制的全球精英人才获取操作系统 (Global Recruitment Operating System)</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("### 🎯 战略目标 (The Strategy)")
        st.write('通过 **\u201c招聘工程学\u201d系统**，实现\u201c流水线式精准捕获\u201d，取代\u201c作坊式招聘\u201d。让非技术背景的 HR 也能像特种部队一样精准捕获海外高端架构师。')
        
        st.markdown("### 🗺️ The Blueprint: 7步闭环全流程地图")
        st.info("""
        **核心闭环节点：**
        1. **需求对齐 (Calibration)**: 消除模糊画像，输出《JD 逆向工程表》。
        2. **多渠道寻源 (Sourcing)**: 使用 X-Ray Boolean Strings，实现 10 倍搜索效率。
        3. **自动化触达 (Outreach)**: 高转化率的邀约文案。
        4. **结构化面试 (Vetting)**: 统一面试官标准，采用《结构化评分卡(Scorecard)》。
        5. **决策反馈 (Decision)**: 基于打分板的数据驱动决策。
        6. **Offer 谈判 (Offer & Closing)**: 薪酬博弈与入职期望管理。
        7. **复盘优化 (Retro)**: 迭代渠道与画像。
        """)
        
    with col2:
        st.markdown("### 💡 快速开始")
        st.markdown("""
        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; border-left: 4px solid #004D99; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1);">
        <h4 style="color: #004D99; margin-top: 0;">第 1 步：生成职位描述</h4>
        <p style="color: #4B5563; font-size: 0.95rem;">前往左侧 <b>[模块一]</b>，输入业务线的核心挑战和红线要求，AI 将自动输出具备高转化率的 JD 和猎头级寻源代码。</p>
        <hr style="border-top: 1px solid #E5E7EB;">
        <h4 style="color: #004D99;">第 2 步：构建面试标准</h4>
        <p style="color: #4B5563; font-size: 0.95rem;">前往 <b>[模块二]</b>，将生成的 JD 传入系统，一键生成带有 STAR 面试题库的量化打分板，统一全球面试官的"度量衡"。</p>
        <hr style="border-top: 1px solid #E5E7EB;">
        <h4 style="color: #004D99;">第 3 步：合规与政策查询</h4>
        <p style="color: #4B5563; font-size: 0.95rem;">在 <b>[模块三]</b>，您可以随时向 AI 询问《Alauda 出海招聘手册》中的内容，例如各地薪资结构、期权发放政策等。</p>
        </div>
        """, unsafe_allow_html=True)


elif page == "📋 模块零：HC 业务需求审批":
    st.markdown('<div class="main-title">📋 业务线 HC 需求提报与审批</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">打造业务部门与 HR 的协同桥梁。业务方在此提报人才需求，HR 审批通过后自动流转至“JD 生成与寻源”模块。</div>', unsafe_allow_html=True)

    hc_mgr = HCManager()

    tab1, tab2 = st.tabs(["📤 我是业务：提报新 HC", "✅ 我是 HR：审批 HC 需求"])

    with tab1:
        st.markdown("### 业务线需求申请表")
        st.info(
            "🌐 **语言说明：** 支持中文或英文填写。\n\n"
            "- 如果您用**英文**填写，内容将直接保存并流转至后续模块。\n"
            "- 如果您用**中文**填写，系统提交时会**自动翻译成英文**再保存，"
            "确保 JD 生成和 X-Ray 寻源获得最佳效果。"
        )
        with st.form("hc_request_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                department = st.selectbox("需求部门", ["云原生研发中心", "全球交付中心", "海外售前团队"])
                role_title = st.text_input("Role Title（岗位名称）", placeholder="E.g.: Technical Service Manager — Singapore")
                location = st.text_input("Target Location（工作地点）", placeholder="E.g.: Singapore / Malaysia / Remote APAC")
            with col_b:
                urgency = st.select_slider("紧急程度", options=["🔥 Low priority", "🔥🔥 Normal", "🔥🔥🔥 Critical — project blocked on hire"])

            mission = st.text_area("1️⃣ The Mission — what must this person deliver in Year 1? *", placeholder="E.g.: Lead 2 enterprise OpenShift replacement projects for financial clients in Singapore; build a standardized English-language delivery runbook.", height=80)
            tech_stack = st.text_input("2️⃣ Required Tech Stack（必须技术，逗号分隔）*", placeholder="E.g.: Kubernetes, OpenShift, Docker, Terraform, CI/CD, Linux")
            deal_breakers = st.text_input("3️⃣ Deal Breakers — hard disqualifiers（红线）", placeholder="E.g.: No business-level English; unwilling to travel; no B2B enterprise experience")
            selling_point = st.text_input("4️⃣ Selling Point — why should top talent join?（核心卖点）", placeholder="E.g.: High-caliber APAC clients; cutting-edge cloud-native stack; uncapped performance compensation")
            
            submit_hc = st.form_submit_button("🚀 提交 HC 申请", type="primary")
            if submit_hc:
                if not role_title or not mission or not tech_stack:
                    st.error("请完整填写标有 * 的必填项！")
                else:
                    import re as _re
                    def _has_chinese(text):
                        return bool(_re.search(r'[\u4e00-\u9fff]', str(text)))

                    fields = {
                        "role_title": role_title,
                        "location": location,
                        "mission": mission,
                        "tech_stack": tech_stack,
                        "deal_breakers": deal_breakers,
                        "selling_point": selling_point,
                    }
                    needs_translation = any(_has_chinese(v) for v in fields.values())

                    if needs_translation and os.getenv("OPENAI_API_KEY"):
                        with st.spinner("🌐 检测到中文内容，正在自动翻译为英文..."):
                            translated = agent.translate_hc_fields(fields)
                        role_title    = translated.get("role_title", role_title)
                        location      = translated.get("location", location)
                        mission       = translated.get("mission", mission)
                        tech_stack    = translated.get("tech_stack", tech_stack)
                        deal_breakers = translated.get("deal_breakers", deal_breakers)
                        selling_point = translated.get("selling_point", selling_point)
                        st.success("✅ 已自动翻译为英文，以下是翻译后保存的内容：")
                        with st.expander("📄 查看翻译结果", expanded=True):
                            st.markdown(f"**Mission:** {mission}")
                            st.markdown(f"**Deal Breakers:** {deal_breakers}")
                            st.markdown(f"**Selling Point:** {selling_point}")

                    hc_mgr.submit_request(department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point)
                    st.success("✅ HC 申请已提交！等待 HR BP 审批。")

    with tab2:
        st.markdown("### HR BP 审批工作台")
        requests = hc_mgr.get_all_requests()
        if not requests:
            st.info("当前没有任何 HC 申请。")
        else:
            for req in requests:
                status_color = "#F59E0B" if req['status'] == "Pending" else ("#10B981" if req['status'] == "Approved" else "#EF4444")
                status_icon = "⏳ 待审批" if req['status'] == "Pending" else ("✅ 已批准" if req['status'] == "Approved" else "❌ 已驳回")
                
                with st.expander(f"{req['date']} | {req['department']} - {req['role_title']} [{status_icon}]"):
                    st.markdown(f"**地点**: {req['location']} &nbsp;&nbsp;|&nbsp;&nbsp; **紧急度**: {req['urgency']}")
                    st.markdown(f"**使命**: {req['mission']}")
                    st.markdown(f"**技术栈**: {req['tech_stack']}")
                    st.markdown(f"**红线**: {req['deal_breakers']} &nbsp;&nbsp;|&nbsp;&nbsp; **卖点**: {req['selling_point']}")
                    
                    if req['status'] == "Pending":
                        c1, c2 = st.columns([1, 10])
                        with c1:
                            if st.button("批准", key=f"approve_{req['id']}", type="primary"):
                                hc_mgr.update_status(req['id'], "Approved")
                                st.rerun()
                        with c2:
                            if st.button("驳回", key=f"reject_{req['id']}"):
                                hc_mgr.update_status(req['id'], "Rejected")
                                st.rerun()

elif page == "🎯 模块一：JD 逆向与自动寻源":
    st.markdown('<div class="main-title">🎯 JD 逆向工程与自动化寻源</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">承接业务线的 HC 需求，AI 将自动输出“高转化率的职位描述 (JD)”与“Google X-Ray 自动化寻源代码”。</div>', unsafe_allow_html=True)
    
    hc_mgr = HCManager()
    approved_hcs = hc_mgr.get_approved_requests()
    
    # 构造下拉列表选项
    hc_options = ["— 手动创建新职位 (不关联 HC) —"]
    hc_mapping = {}
    for hc in approved_hcs:
        label = f"[{hc['department']}] {hc['role_title']} ({hc['location']})"
        hc_options.append(label)
        hc_mapping[label] = hc
        
    st.markdown("### 选择业务线已批准的 HC 需求")
    selected_hc_label = st.selectbox("流转来源", hc_options)
    
    # 如果选择了某个 HC，自动填充默认值
    def_role = "Global Presales Architect"
    def_loc = "Singapore / Remote APAC"
    def_mission = "What are the 3 key outcomes this person must deliver in Year 1?\nE.g.: Lead 2 enterprise OpenShift replacement deals worth $1M+; build a standardized English-language delivery toolkit."
    def_tech = "Kubernetes, Docker, CI/CD, Go/Python, AWS/Azure"
    def_breakers = "Hard disqualifiers — no exceptions.\nE.g.: Cannot conduct full technical presentations in fluent English; no B2B enterprise software delivery experience."
    def_selling = "Why should a top engineer leave their comfort zone to join Alauda?\nE.g.: Cloud-native global expansion wave; direct challenge against Red Hat; uncapped performance compensation."
    
    if selected_hc_label != "— 手动创建新职位 (不关联 HC) —":
        hc_data = hc_mapping[selected_hc_label]
        def_role = hc_data['role_title']
        def_loc = hc_data['location']
        def_mission = hc_data['mission']
        def_tech = hc_data['tech_stack']
        def_breakers = hc_data['deal_breakers']
        def_selling = hc_data['selling_point']
        st.info(f"💡 已自动为您填入业务线提交的原始需求信息，您可以作为 HR 进行进一步的专业润色后再生成 JD。")

    st.info("🇬🇧 **Language guidance:** Please fill in all fields below in **English**. English inputs give the AI access to a much richer global talent knowledge base and produce higher-quality JDs and Boolean search strings.")

    with st.form("jd_calibration_form", clear_on_submit=False):
        st.markdown("### The Calibration Protocol")

        col1, col2 = st.columns(2)
        with col1:
            role_title = st.text_input("Role Title", value=def_role)
            location = st.text_input("Target Location", value=def_loc)
            mission = st.text_area("1️⃣ The Mission — Year-1 business objectives *", value=def_mission, height=120)

        with col2:
            tech_stack = st.text_input("2️⃣ The Tech Stack — required technologies *", value=def_tech)
            deal_breakers = st.text_area("3️⃣ The Deal Breakers — hard disqualifiers *", value=def_breakers, height=120)

        selling_point = st.text_area("4️⃣ The Selling Point — why join Alauda", value=def_selling, height=80)
        
        submitted = st.form_submit_button("🚀 运行系统：一键生成 JD 与寻源方案", type="primary", use_container_width=True)
        
    if submitted:
        if not os.getenv("OPENAI_API_KEY"):
            st.error("您尚未配置大模型 API Key。请前往系统根目录的 `.env` 文件进行配置。")
        else:
            with st.spinner("🤖 The Sourcing Engine 正在运转，预计需要 10-15 秒，请稍候..."):
                result = agent.generate_jd_and_xray(
                    role_title, location, mission, tech_stack, deal_breakers, selling_point
                )
                
                st.session_state["generated_jd"] = result
                st.success("✅ 生成完成！结果已自动保存到系统缓存中，供下一步（打分卡）调用。")
                
                st.markdown("### 📄 最终交付物")
                st.markdown(f'<div style="background-color: #FFFFFF; padding: 30px; border-radius: 8px; border: 1px solid #E5E7EB;">{result}</div>', unsafe_allow_html=True)
                
                if result:
                    st.download_button(
                        label="📥 下载 Markdown 源文件",
                        data=result,
                        file_name=f"Alauda_GROS_{role_title.replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=False
                    )

elif page == "✉️ 模块二：自动化触达 (Outreach)":
    st.markdown('<div class="main-title">✉️ 高转化率自动化触达 (Cold Outreach)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">抛弃“我们在招人，你有兴趣吗”的废话，一键生成直击痛点、高度个性化的猎头级触达邮件与 LinkedIn InMail。</div>', unsafe_allow_html=True)

    default_jd_text = ""
    if "generated_jd" in st.session_state:
        default_jd_text = st.session_state["generated_jd"]
        st.info("💡 系统已自动读取您在【模块一】生成的职位画像。")
    else:
        st.warning("建议先去【模块一】生成职位描述，或者在下方手动粘贴 JD 核心信息。")

    st.info("🇬🇧 **Language guidance:** Fill in candidate background in **English** — the outreach copy targets overseas engineers and benefits most from English-language inputs.")

    with st.form("outreach_form"):
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**1. Job Context (JD)**")
            jd_input = st.text_area("Job description / core mission", value=default_jd_text, height=250)

        with col2:
            st.markdown("**2. Candidate Intelligence** — for personalized opening")
            candidate_name = st.text_input("Candidate name (e.g. John Doe)")
            candidate_bg = st.text_area("Candidate highlights / background (from resume or LinkedIn)", placeholder="E.g.: 3 years at Red Hat, led OpenShift deployment at a major bank; recently open-sourced a Kubernetes scheduling plugin on GitHub with 200+ stars...", height=170)

        submitted = st.form_submit_button("✉️ 生成英文触达话术 (Email & InMail)", type="primary", use_container_width=True)

    if submitted:
        if not os.getenv("OPENAI_API_KEY"):
            st.error("您尚未配置大模型 API Key。")
        else:
            with st.spinner("🤖 正在运用 Alex Hormozi 的 Acquisition 营销框架构思文案..."):
                candidate_info = f"姓名: {candidate_name}\n背景亮点: {candidate_bg}"
                outreach_result = agent.generate_outreach_message(jd_input, candidate_info)
                
                st.success("✅ 触达文案生成完毕！您可以直接复制发送。")
                st.markdown(f'<div style="background-color: #FFFFFF; padding: 30px; border-radius: 8px; border: 1px solid #E5E7EB;">{outreach_result}</div>', unsafe_allow_html=True)


elif page == "📄 模块三：简历智能初筛 (Resume Matcher)":
    st.markdown('<div class="main-title">📄 猎头简历智能雷达 (Resume Matcher)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">解决 HR 看不懂海外技术简历、容易被候选人过度包装忽悠的问题。AI 基于严苛的【算分卡法则】进行防漂移量化打分。</div>', unsafe_allow_html=True)

    # 左右两栏布局：左边 JD，右边简历上传
    col_jd, col_resume = st.columns([1, 1])

    with col_jd:
        st.markdown("### 🎯 Benchmark: Job Description")
        default_jd_for_match = ""
        if "generated_jd" in st.session_state:
            default_jd_for_match = st.session_state["generated_jd"]
            st.info("💡 Auto-loaded from Module 1. You may edit before running evaluation.")
        else:
            st.warning("Recommend generating a JD in Module 1 first, or paste an English JD below.")
        st.caption("🇬🇧 Use an English JD for best results — the scoring rubric and resume comparison both perform better in a single language.")
        jd_for_match = st.text_area("Paste or edit JD content", value=default_jd_for_match, height=350, key="resume_jd_input")

    with col_resume:
        st.markdown("### 📤 批量上传候选人简历")
        uploaded_resumes = st.file_uploader(
            "支持 PDF / TXT 格式，可同时上传多份",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key="resume_uploader"
        )
        if uploaded_resumes:
            st.success(f"已上传 {len(uploaded_resumes)} 份简历，点击下方按钮开始评估。")

    if st.button("🚀 启动硬核评估 (AI 算分卡)", type="primary", use_container_width=True):
        if not jd_for_match.strip():
            st.error("请先在左侧填入职位描述 (JD) 作为评估基准！")
        elif not uploaded_resumes:
            st.error("请先在右侧上传至少一份候选人简历！")
        elif not os.getenv("OPENAI_API_KEY"):
            st.error("您尚未配置大模型 API Key。")
        else:
            st.markdown("---")
            st.markdown("### 📊 评估结果")
            for i, resume_file in enumerate(uploaded_resumes):
                file_bytes = resume_file.read()
                file_name = resume_file.name
                with st.spinner(f"🤖 正在评估第 {i+1}/{len(uploaded_resumes)} 份简历：{file_name}..."):
                    resume_text = agent.extract_text_from_file(file_name, file_bytes)
                    if resume_text.startswith("文件解析失败") or resume_text == "Unsupported file format.":
                        st.error(f"❌ {file_name}: {resume_text}")
                        continue
                    result = agent.evaluate_resume(jd_for_match, resume_text)

                with st.expander(f"📄 {file_name}", expanded=True):
                    st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E7EB;">{result}</div>', unsafe_allow_html=True)

            st.success(f"✅ 全部 {len(uploaded_resumes)} 份简历评估完毕！")


elif page == "📝 模块四：结构化面试打分卡":
    st.markdown('<div class="main-title">📝 结构化面试评估系统</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">消除面试过程中的主观偏见。基于 JD 自动提取关键维度，生成【行为锚定评分卡 (Scorecard)】与【STAR 题库】。</div>', unsafe_allow_html=True)
    
    default_jd_text = ""
    if "generated_jd" in st.session_state:
        default_jd_text = st.session_state["generated_jd"]
        st.info("💡 Auto-loaded the JD generated in Module 1. You may edit before generating the scorecard.")
    else:
        st.warning("No JD found. Recommend generating one in Module 1 first, or paste an English JD below.")
        default_jd_text = ""

    st.caption("🇬🇧 English JD recommended — BARS anchors and STAR questions are drawn from English-world interviewing literature and will be significantly more precise.")
    jd_input = st.text_area("Job Description source:", value=default_jd_text, height=350)
    
    if st.button("⚖️ 拆解能力模型并生成 Scorecard", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("您尚未配置大模型 API Key。")
        else:
            with st.spinner("🤖 正在为您量身定制结构化面试题库及评分标准..."):
                scorecard_result = agent.generate_interview_scorecard(jd_input)
                st.success("✅ 评分卡建立完毕！请在面试前分发给所有面试官统一评价口径。")
                
                st.markdown("### 📊 结构化打分板")
                st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E7EB;">{scorecard_result}</div>', unsafe_allow_html=True)
                
                if scorecard_result:
                    st.download_button(
                        label="📥 下载评估表单 (Markdown)",
                        data=scorecard_result,
                        file_name="Alauda_Interview_Scorecard.md",
                        mime="text/markdown",
                    )

elif page == "📚 模块五：Playbook 智库问答":
    st.markdown('<div class="main-title">📚 灵雀云出海智库 AI 助手</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">基于 RAG 检索增强技术。您可以随时询问关于本地化合规、出海战略指导手册、雇主品牌沟通话术等内容。</div>', unsafe_allow_html=True)
    
    from document_parser import RAGSystem
    
    @st.cache_resource
    def get_rag_system():
        return RAGSystem()
        
    rag = get_rag_system()
    
    with st.spinner("⏳ 正在挂载本地知识库 (PDF & 动态沉淀库)..."):
        is_loaded = rag.load_and_index()

    if not is_loaded:
        st.error("❌ 知识库引擎启动失败，未找到可加载的文档。")
    else:
        if rag.embedding_mode == "vector":
            st.success("✅ 知识库已就绪 — **向量语义搜索模式**（全精度）")
        else:
            st.warning(
                "⚠️ 知识库已就绪，但当前运行在**关键词降级模式**（语义相似度未启用）。\n\n"
                "如需开启全精度向量检索，请在 `.env` 中配置：\n"
                "```\nEMBEDDING_API_KEY=your_openai_compatible_key\n"
                "EMBEDDING_API_BASE=https://api.openai.com/v1\n```"
            )
    
    chat_container = st.container()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("您可以向知识库提问，例如：'海外交付工程师的考核 KPI 有哪些？'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not is_loaded:
                    st.warning("对不起，向量化引擎尚未准备好，请查看页面上方提示进行配置。")
                else:
                    with st.spinner("🔍 正在检索 Playbook 与动态经验库相关段落..."):
                        context_docs = rag.retrieve(prompt)
                        if not context_docs:
                            st.warning("⚠️ 在当前知识库中没有检索到与此问题强相关的原始段落。AI 的回答可能缺乏确切依据。")
                            
                    with st.spinner("🤖 正在基于内部文件构思专业回答..."):
                        response = agent.answer_playbook_question(prompt, context_docs)
                    
                    st.markdown(response)
                    
                    if context_docs:
                        with st.expander("📝 溯源：查看检索到的原始文件段落"):
                            st.text(context_docs)
                        
            st.session_state.messages.append({"role": "assistant", "content": response})

elif page == "🏗️ 模块六：知识库自生长 (0-to-1)":
    st.markdown('<div class="main-title">🏗️ 知识库全自动收割机 (Web Auto-Harvester)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">告别人工录入！只需输入权威政策网页或竞品招聘网址，AI 爬虫将自动提取、清洗并将其沉淀为结构化的本地知识库。</div>', unsafe_allow_html=True)

    km = KnowledgeManager()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🕸️ 方式一：AI 网页情报自动抓取")
        with st.form("auto_harvester_form", clear_on_submit=True):
            # 提供权威信息源快捷下拉填充
            official_urls = {
                "自定义输入 (或直接在下方粘贴 URL)": "",
                "🇸🇬 新加坡 EP 签证 COMPASS 计分制 (解析版)": "https://sg.acclime.com/guides/singapore-employment-pass/",
                "🇸🇬 新加坡 CPF (公积金) 费率政策 (普华永道解析)": "https://taxsummaries.pwc.com/singapore/individual/other-taxes",
                "🇲🇾 马来西亚最新劳工法修正案 (法律解析)": "https://www.taypartners.com.my/employment-act-1955-key-amendments-2023/",
                "🇲🇾 马来西亚外籍专才 EP 签证申请指南": "https://www.paulhypepage.my/guide/malaysia-employment-pass/",
                "🇭🇰 香港“高才通”与专才签证对比 (毕马威指南)": "https://www.pwccn.com/zh/services/tax/publications/tax-news-mar2024-1.html",
                "🇭🇰 香港雇佣条例与解雇规定 (Deacons)": "https://www.deacons.com/zh-hant/news-and-insights/publications/employment-law-in-hong-kong-frequently-asked-questions/",
                "🇿🇦 南非外籍关键技能签证 (Critical Skills) 解析": "https://www.xpatweb.com/south-africa-critical-skills-visa/",
                "🇿🇦 南非解雇与劳动法实务 (Bowmans)": "https://www.bowmanslaw.com/insights/employment/south-africa-terminating-employment/"
            }
            
            selected_preset = st.selectbox("💡 快速选择官方信息源 (自动填充链接)", list(official_urls.keys()))
            default_url = official_urls[selected_preset]
            
            target_url = st.text_input("🔗 目标网页 URL", value=default_url, placeholder="或在此处直接粘贴任何网页链接...")
            region = st.selectbox("归属区域", ["Singapore", "Malaysia", "South Africa", "Middle East", "Global/General"])
            category = st.selectbox("情报分类", ["官方政策法规 (Official Law)", "薪酬与竞品情报 (Market Intel)", "签证与工作许可 (Visa/EP)", "其他避雷指南"])
            
            submitted_url = st.form_submit_button("🤖 启动爬虫并提取知识", type="primary")
            
            if submitted_url:
                if not target_url.strip() or not target_url.startswith("http"):
                    st.error("请输入有效的网页链接（需包含 http:// 或 https://）")
                else:
                    if not os.getenv("OPENAI_API_KEY"):
                        st.error("缺失大模型 API Key，无法进行内容清洗。")
                    else:
                        with st.spinner(f"正在爬取 {target_url} 的内容..."):
                            try:
                                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.5'}
                                response = requests.get(target_url, headers=headers, timeout=10, verify=False)
                                response.raise_for_status()
                                
                                soup = BeautifulSoup(response.text, 'html.parser')
                                for script in soup(["script", "style", "nav", "footer"]):
                                    script.decompose()
                                
                                raw_text = soup.get_text(separator=' ', strip=True)
                                
                                if len(raw_text) < 50:
                                    st.error("该网页似乎限制了爬虫或内容过少，未能抓取到有效文本。")
                                else:
                                    st.success(f"✅ 网页爬取成功（共 {len(raw_text)} 字符）。正在交由 AI 进行知识萃取...")
                                    
                                    with st.spinner("🤖 AI extracting core policy intelligence..."):
                                        prompt = f"""
You are an expert in global compliance and recruitment intelligence extraction.
I have scraped the following webpage: {target_url}

From the raw text below, extract 1 to 3 of the most actionable, concrete rules or facts
relevant to [{region}] in the category [{category}].

Requirements:
- Strip all filler content, navigation text, and promotional language
- Output precise, dated facts (salary thresholds, visa quotas, notice periods, etc.)
- If no relevant information is found, respond exactly with: "EXTRACTION_FAILED"
- Respond in English

[Raw scraped text (truncated)]:
{raw_text[:8000]}
"""
                                        
                                        ai_result = agent.client.chat.completions.create(
                                            model=agent.strong_model,
                                            messages=[{"role": "user", "content": prompt}],
                                            temperature=0.2
                                        ).choices[0].message.content
                                        
                                        if "EXTRACTION_FAILED" in ai_result:
                                            st.warning("AI 未能在该网页中找到有价值的情报。")
                                        else:
                                            tags = f"{region}, Auto-Harvested, {category.split(' ')[0]}"
                                            km.add_fragment(region, category, ai_result, tags)
                                            st.success("🎉 知识萃取成功！已自动存入底层数据库。")
                                            st.info("提取到的精华内容如下：\n" + ai_result)
                            except Exception as e:
                                st.error(f"抓取网页时发生错误: {str(e)}")

        st.markdown("---")
        st.markdown("### 📝 方式二：人工补充 (备用)")
        with st.expander("点击展开手工录入面板"):
            with st.form("manual_fragment_form", clear_on_submit=True):
                man_region = st.selectbox("区域", ["Singapore", "Malaysia", "South Africa", "Hong Kong", "Global/General"])
                man_category = st.selectbox("分类", ["薪酬福利", "签证与合规", "本地猎头潜规则"])
                man_content = st.text_area("具体经验", height=100)
                if st.form_submit_button("保存"):
                    if man_content.strip():
                        km.add_fragment(man_region, man_category, man_content, "Manual")
                        st.success("录入成功")

    with col2:
        st.markdown("### 🗂️ 知识库编译中心")
        st.info("无论是 AI 网页爬虫还是人工录入获取的情报，都需要点击下方按钮进行统一编译。编译后，RAG 大脑才能读取到这些最新知识。")
        
        if st.button("🚀 编译 Playbook 并同步至 RAG 引擎", type="primary", use_container_width=True):
            with st.spinner("正在将零散情报汇编为结构化 Markdown 库..."):
                success = km.compile_to_markdown()
                if success:
                    from document_parser import invalidate_rag_index
                    invalidate_rag_index()
                    st.success("✅ 动态 Playbook 编译完成！RAG 引擎已自动刷新，新知识立即生效。")
                    st.info("💡 现在可直接前往【模块五】提问，无需重启系统。")
                else:
                    st.warning("目前数据库中没有任何情报。")
                    
        st.markdown("---")
        fragments = km.get_all_fragments()
        if not fragments:
            st.info("知识情报库目前为空。请在左侧输入网址让 AI 去收割。")
        else:
            st.write(f"当前库中共有 **{len(fragments)}** 条高价值情报：")
            with st.container(height=450):
                for f in fragments:
                    tag_str = ", ".join(f.get('tags', []))
                    st.markdown(f"""
                    <div style="background-color: #FFFFFF; padding: 15px; border-radius: 6px; border: 1px solid #E2E8F0; margin-bottom: 10px; border-left: 3px solid #004D99;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <strong>{f['region']} - {f['category']}</strong>
                            <span style="color: #6B7280; font-size: 0.8em;">{f['date']}</span>
                        </div>
                        <p style="color: #4B5563; font-size: 0.9em; margin: 0;">{f['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
# trigger rebuild
