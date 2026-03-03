import streamlit as st
from app_shared import bi

st.markdown('<div class="main-title">🌍 Alauda Global Elite Recruitment Command Center / 灵雀云全球精英招聘指挥中心</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">A Replicable Global Elite Talent Acquisition Operating System / 可复制的全球精英人才获取操作系统 (GROS)</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown("### 🎯 The Strategy / 战略目标")
    st.write('Replace "artisan recruiting" with a **"Recruitment Engineering"** system for pipeline-style precision capture. Enable non-technical HR to capture elite overseas architects like a special operations unit.\n\n通过 **\u201c招聘工程学\u201d系统**，实现\u201c流水线式精准捕获\u201d，取代\u201c作坊式招聘\u201d。让非技术背景的 HR 也能像特种部队一样精准捕获海外高端架构师。')

    st.markdown("### 🗺️ The Blueprint: 7-Step Closed-Loop Pipeline / 7步闭环全流程地图")
    st.info("""
    **Core Pipeline Nodes / 核心闭环节点：**
    1. **Calibration / 需求对齐**: Eliminate vague profiles → output JD Reverse-Engineering Sheet / 消除模糊画像，输出《JD 逆向工程表》
    2. **Sourcing / 多渠道寻源**: X-Ray Boolean Strings for 10x search efficiency / 使用 X-Ray Boolean Strings，实现 10 倍搜索效率
    3. **Outreach / 自动化触达**: High-conversion cold outreach copy / 高转化率的邀约文案
    4. **Vetting / 结构化面试**: Unified Scorecard standard for all interviewers / 统一面试官标准，采用《结构化评分卡》
    5. **Decision / 决策反馈**: Data-driven decisions based on scorecards / 基于打分板的数据驱动决策
    6. **Offer & Closing / Offer 谈判**: Comp negotiation & onboarding expectation management / 薪酬博弈与入职期望管理
    7. **Retro / 复盘优化**: Iterate channels & candidate profiles / 迭代渠道与画像
    """)

with col2:
    st.markdown("### 💡 Quick Start / 快速开始")
    st.markdown("""
    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; border-left: 4px solid #004D99; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1);">
    <h4 style="color: #004D99; margin-top: 0;">Step 1: Generate JD / 第 1 步：生成职位描述</h4>
    <p style="color: #4B5563; font-size: 0.95rem;">Go to <b>[Module 1]</b> on the left. Input your business line's core challenges and deal breakers — AI will auto-generate a high-conversion JD and recruiter-grade sourcing code.<br>前往左侧 <b>[模块一]</b>，输入业务线的核心挑战和红线要求，AI 将自动输出具备高转化率的 JD 和猎头级寻源代码。</p>
    <hr style="border-top: 1px solid #E5E7EB;">
    <h4 style="color: #004D99;">Step 2: Build Interview Standards / 第 2 步：构建面试标准</h4>
    <p style="color: #4B5563; font-size: 0.95rem;">Go to <b>[Module 4]</b>. Feed in the generated JD to produce a quantified scorecard with STAR question bank, unifying the 'measurement standard' for all interviewers globally.<br>前往 <b>[模块四]</b>，将生成的 JD 传入系统，一键生成带有 STAR 面试题库的量化打分板，统一全球面试官的\u201c度量衡\u201d。</p>
    <hr style="border-top: 1px solid #E5E7EB;">
    <h4 style="color: #004D99;">Step 3: Compliance & Policy Q&A / 第 3 步：合规与政策查询</h4>
    <p style="color: #4B5563; font-size: 0.95rem;">In <b>[Module 5]</b>, ask AI anytime about the Alauda Global Recruitment Playbook — local salary structures, stock option policies, visa requirements, etc.<br>在 <b>[模块五]</b>，您可以随时向 AI 询问《Alauda 出海招聘手册》中的内容，例如各地薪资结构、期权发放政策等。</p>
    </div>
    """, unsafe_allow_html=True)
