import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd

# 强制覆盖环境变量
load_dotenv(override=True)

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
        st.write("通过 **“招聘工程学”系统**，实现“流水线式精准捕获”，取代“作坊式招聘”。让非技术背景的 HR 也能像特种部队一样精准捕获海外高端架构师。")
        
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
        <p style="color: #4B5563; font-size: 0.95rem;">前往 <b>[模块二]</b>，将生成的 JD 传入系统，一键生成带有 STAR 面试题库的量化打分板，统一全球面试官的“度量衡”。</p>
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
        st.markdown("请用大白话描述你要解决的业务问题，不需要你写专业的 JD，系统后续会自动帮你写。")
        with st.form("hc_request_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                department = st.selectbox("需求部门", ["海外出海战略部", "云原生研发中心", "全球交付交付中心", "其他支持部门"])
                role_title = st.text_input("岗位名称 (俗称即可)", placeholder="比如：新加坡懂K8s的售前")
                location = st.text_input("工作地点", placeholder="Singapore / Remote")
            with col_b:
                urgency = st.select_slider("紧急程度", options=["🔥 不急", "🔥🔥 正常", "🔥🔥🔥 极其紧急 (项目等米下锅)"])
                
            mission = st.text_area("1️⃣ 核心使命 (入职第一年要解决什么最大的麻烦？) *", placeholder="比如：搞定两个当地金融客户的 OpenShift 替换项目...", height=80)
            tech_stack = st.text_input("2️⃣ 必须掌握的核心技术 (逗号分隔) *", placeholder="Kubernetes, Go, AWS")
            deal_breakers = st.text_input("3️⃣ 绝对不能接受的特质 (红线)", placeholder="英文不行、不能出差")
            selling_point = st.text_input("4️⃣ 你能给候选人画什么饼 (核心卖点)", placeholder="跟着我打天下，提成不设上限")
            
            submit_hc = st.form_submit_button("🚀 提交 HC 申请", type="primary")
            if submit_hc:
                if not role_title or not mission or not tech_stack:
                    st.error("请完整填写标有 * 的必填项！")
                else:
                    hc_mgr.submit_request(department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point)
                    st.success(f"✅ HC 申请已提交！等待 HR BP 审批。")

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
    def_role = "Global Presales Architect (售前架构师)"
    def_loc = "Singapore / Remote APAC"
    def_mission = "入职第一年必须完成的 3 个关键任务是什么？\n例：主导 2 个千万级金融客户的 OpenShift 替代方案打单；建立一套标准化英文交付材料。"
    def_tech = "Kubernetes, Docker, CI/CD, Go/Python, AWS/Azure"
    def_breakers = "绝对不能接受的特质。例：无法流畅进行全英文技术路演；没有 ToB 软件企业级服务经验。"
    def_selling = "为什么顶级人才要离开现在的舒适区来 Alauda？\n例：云原生出海红利期，直接挑战 Red Hat 的产品力，无天花板的薪酬体系。"
    
    if selected_hc_label != "— 手动创建新职位 (不关联 HC) —":
        hc_data = hc_mapping[selected_hc_label]
        def_role = hc_data['role_title']
        def_loc = hc_data['location']
        def_mission = hc_data['mission']
        def_tech = hc_data['tech_stack']
        def_breakers = hc_data['deal_breakers']
        def_selling = hc_data['selling_point']
        st.info(f"💡 已自动为您填入业务线提交的原始需求信息，您可以作为 HR 进行进一步的专业润色后再生成 JD。")

    with st.form("jd_calibration_form", clear_on_submit=False):
        st.markdown("### The Calibration Protocol (精准画像输入协议)")
        
        col1, col2 = st.columns(2)
        with col1:
            role_title = st.text_input("招聘岗位头衔", value=def_role)
            location = st.text_input("目标工作地点", value=def_loc)
            mission = st.text_area("1️⃣ The Mission (核心使命) *", value=def_mission, height=120)
            
        with col2:
            tech_stack = st.text_input("2️⃣ The Tech Stack (必须技术栈) *", value=def_tech)
            deal_breakers = st.text_area("3️⃣ The Deal Breakers (绝对红线) *", value=def_breakers, height=120)
            
        selling_point = st.text_area("4️⃣ The Selling Point (核心卖点 / Alauda 优势)", value=def_selling, height=80)
        
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

    with st.form("outreach_form"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**1. 目标职位信息 (JD)**")
            jd_input = st.text_area("职位画像/核心挑战", value=default_jd_text, height=250)
            
        with col2:
            st.markdown("**2. 候选人情报 (用于个性化“破冰”)**")
            candidate_name = st.text_input("候选人称呼 (如: John Doe)")
            candidate_bg = st.text_area("候选人亮点/背景 (从简历或领英提取)", placeholder="例如：曾在 Red Hat 工作 3 年，主导过当地银行的 OpenShift 落地项目；最近在 GitHub 上开源了一个 Kubernetes 调度插件...", height=170)

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


elif page == "📝 模块四：结构化面试打分卡":
    st.markdown('<div class="main-title">📝 结构化面试评估系统</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">消除面试过程中的主观偏见。基于 JD 自动提取关键维度，生成【行为锚定评分卡 (Scorecard)】与【STAR 题库】。</div>', unsafe_allow_html=True)
    
    default_jd_text = ""
    if "generated_jd" in st.session_state:
        default_jd_text = st.session_state["generated_jd"]
        st.info("💡 系统已自动捕获您在【模块一】生成的 JD 文本。您可以直接使用该 JD，或进行手动修改。")
    else:
        st.warning("您还未生成职位描述。建议先去【模块一】生成，或者在此处手动粘贴外部的职位要求。")
        default_jd_text = "请在此粘贴完整的职位要求与业务背景..."
        
    jd_input = st.text_area("Job Description 内容源：", value=default_jd_text, height=350)
    
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
        # 强制清除之前的缓存状态，保证模块四刚生成的文件能被读到
        rag.vector_store = None 
        is_loaded = rag.load_and_index()
        
    if not is_loaded:
        st.error("❌ 知识库引擎启动失败。")
        st.info("""
        **诊断信息：**
        系统需要文本向量化（Embedding）服务来解析您的 PDF 和碎片。由于 DeepSeek 官方暂不提供此接口，请在系统根目录的 `.env` 文件中补充以下配置：
        ```env
        EMBEDDING_API_KEY=您的_兼容_OpenAI_格式的_Embedding_Key
        EMBEDDING_API_BASE=对应的API地址
        ```
        """)
    else:
        st.info("✅ 已成功挂载《Alauda Global Recruitment Playbook》以及您的动态经验碎片。您可以开始提问。")
    
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
    st.markdown('<div class="main-title">🏗️ 知识库自生长 (Knowledge Builder)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">解决“没有现成的手册怎么办”的问题。在招聘实战中将零散的踩坑经验碎片化录入，系统将自动汇编、向量化，形成企业专属动态 Playbook。</div>', unsafe_allow_html=True)

    km = KnowledgeManager()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 录入新经验碎片")
        with st.form("add_fragment_form", clear_on_submit=True):
            region = st.selectbox("区域 (Region)", ["Singapore", "Malaysia", "South Africa", "Middle East", "Global/General"])
            category = st.selectbox("经验分类 (Category)", ["薪酬福利与发薪", "签证与工作许可 (Visa/EP)", "候选人寻源渠道", "雇主品牌包装", "劳动法与试用期规定", "其他坑与避雷指南"])
            content = st.text_area("具体经验与规定细节 *", placeholder="例如：新加坡 EP 签证最新打分制 (COMPASS) 规定，薪资需要达到 5000 SGD，且如果在短缺职业清单内可加分...", height=150)
            tags = st.text_input("标签 (Tags, 逗号分隔)", placeholder="EP, COMPASS, Visa")
            
            submitted = st.form_submit_button("💾 保存经验碎片", type="primary")
            if submitted:
                if not content.strip():
                    st.error("内容不能为空！")
                else:
                    km.add_fragment(region, category, content, tags)
                    st.success("✅ 碎片录入成功！")
                    
        st.markdown("---")
        st.markdown("### 🔄 编译与同步至 AI 引擎")
        st.write("当您录入了一批新的经验后，请点击下方按钮，系统将把碎片整合为标准 Markdown 文档，供 RAG 引擎在【模块三】中搜索回答。")
        if st.button("🚀 编译动态 Playbook 并更新向量库", type="primary", use_container_width=True):
            with st.spinner("正在汇总碎片文件..."):
                success = km.compile_to_markdown()
                if success:
                    st.success("✅ 动态 Playbook 已生成 (存放在 data/Alauda_Dynamic_Playbook.md)")
                    st.info("💡 提示：前往【模块三】提问，AI 现在已经能读取到您刚刚输入的新规则了！")
                else:
                    st.warning("暂无数据可编译。")

    with col2:
        st.markdown("### 🗂️ 已沉淀的碎片一览")
        fragments = km.get_all_fragments()
        
        if not fragments:
            st.info("您的经验库目前为空。请在左侧表单开始录入您的第一个招聘踩坑记录。")
        else:
            st.write(f"共沉淀了 **{len(fragments)}** 条经验规则：")
            
            # 使用一个滚动容器展示
            with st.container(height=500):
                for f in fragments:
                    st.markdown(f"""
                    <div style="background-color: #FFFFFF; padding: 15px; border-radius: 6px; border: 1px solid #E2E8F0; margin-bottom: 10px; border-left: 3px solid #004D99;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <strong>{f['region']} - {f['category']}</strong>
                            <span style="color: #6B7280; font-size: 0.8em;">{f['date']}</span>
                        </div>
                        <p style="color: #4B5563; font-size: 0.9em; margin: 0;">{f['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)


elif page == "📄 模块三：简历智能初筛 (Resume Matcher)":
    st.markdown('<div class="main-title">📄 猎头简历智能雷达 (Resume Matcher)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">收到猎头推来的成堆简历？不用一份份看。AI 扮演严苛的技术面试官，为您一键挤出水分，标记红线。</div>', unsafe_allow_html=True)

    default_jd_text = ""
    if "generated_jd" in st.session_state:
        default_jd_text = st.session_state["generated_jd"]
        st.info("💡 系统已自动读取您在【模块一】生成的岗位画像作为比对标准。")
    else:
        st.warning("建议先去【模块一】生成岗位画像，或者在下方手动粘贴 JD 核心诉求。")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### 1. 确认岗位测量标尺 (JD)")
        jd_input = st.text_area("职位画像/核心挑战", value=default_jd_text, height=300)

    with col2:
        st.markdown("### 2. 批量上传猎头推荐的简历")
        uploaded_files = st.file_uploader("可一次性拖入多份候选人简历 (PDF/TXT)", type=['pdf', 'txt'], accept_multiple_files=True)
        
        if uploaded_files:
            st.write(f"共上传 {len(uploaded_files)} 份简历。")
            
            if st.button("⚖️ 启动批量硬核评估", type="primary", use_container_width=True):
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("您尚未配置大模型 API Key。")
                else:
                    for idx, uploaded_file in enumerate(uploaded_files):
                        st.markdown(f"#### 📄 候选人 {idx+1}: {uploaded_file.name}")
                        with st.spinner(f"正在深度解析简历 {uploaded_file.name} ..."):
                            file_bytes = uploaded_file.getvalue()
                            resume_text = agent.extract_text_from_file(uploaded_file.name, file_bytes)
                            
                            if "文件解析失败" in resume_text:
                                st.error(f"{uploaded_file.name} 提取失败: {resume_text}")
                            else:
                                with st.spinner(f"🤖 AI 面试官正在为 {uploaded_file.name} 挤水分..."):
                                    evaluation_result = agent.evaluate_resume(jd_input, resume_text)
                                    st.markdown(f'<div style="background-color: #FFFFFF; padding: 25px; border-radius: 8px; border: 1px solid #E5E7EB; border-left: 4px solid #004D99; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 2rem;">{evaluation_result}</div>', unsafe_allow_html=True)


