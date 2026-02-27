import html
import json
import os
import re
import urllib.parse
from datetime import datetime

import streamlit as st

from app_shared import get_agent
from hc_manager import HCManager

st.markdown('<div class="main-title">🎯 JD 逆向工程与自动化寻源</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">承接业务线的 HC 需求，AI 将自动输出"高转化率的职位描述 (JD)"与"Google X-Ray 自动化寻源代码"。</div>', unsafe_allow_html=True)

agent = get_agent()
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
    st.info("💡 已自动为您填入业务线提交的原始需求信息，您可以作为 HR 进行进一步的专业润色后再生成 JD。")

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

            # persist to disk so the JD survives page refreshes
            os.makedirs("data/generated", exist_ok=True)
            jd_record = {
                "role_title": role_title,
                "location": location,
                "generated_at": datetime.now().isoformat(),
                "jd_content": result,
            }
            with open("data/generated/latest_jd.json", "w", encoding="utf-8") as f:
                json.dump(jd_record, f, ensure_ascii=False, indent=2)

            st.success("✅ 生成完成！已自动保存 — 刷新页面或切换模块后仍可在各模块中直接使用。")

            st.markdown("### 📄 最终交付物")
            st.markdown(f'<div style="background-color: #FFFFFF; padding: 30px; border-radius: 8px; border: 1px solid #E5E7EB;">{html.escape(result)}</div>', unsafe_allow_html=True)

            if result:
                st.download_button(
                    label="📥 下载 Markdown 源文件",
                    data=result,
                    file_name=f"Alauda_GROS_{role_title.replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=False
                )

                # extract Boolean strings from code blocks → one-click search links
                code_blocks = re.findall(r'```[^\n]*\n(.*?)```', result, re.DOTALL)
                search_strings = [b.strip() for b in code_blocks if len(b.strip()) > 30]
                if search_strings:
                    st.markdown("---")
                    st.markdown("### 🔍 一键执行寻源搜索")
                    st.caption("点击下方链接直接在浏览器中执行 X-Ray 搜索，无需手动复制粘贴。")
                    for i, s in enumerate(search_strings, 1):
                        url = f"https://www.google.com/search?q={urllib.parse.quote(s)}"
                        cols = st.columns([3, 1])
                        with cols[0]:
                            st.code(s, language="")
                        with cols[1]:
                            st.markdown(f"[🔗 立即搜索]({url})", unsafe_allow_html=False)
