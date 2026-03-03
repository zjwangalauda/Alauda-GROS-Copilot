import os
import re

import streamlit as st

from app_shared import get_agent, _llm_cache_key, bi
from hc_manager import HCManager

st.markdown('<div class="main-title">📋 HC Request Submission & Approval / 业务线 HC 需求提报与审批</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Bridging business units and HR. Submit talent requests here — once approved, they flow into JD Generation & Sourcing.\n打造业务部门与 HR 的协同桥梁。业务方在此提报人才需求，HR 审批通过后自动流转至"JD 生成与寻源"模块。</div>', unsafe_allow_html=True)

hc_mgr = HCManager()
agent = get_agent(_key=_llm_cache_key())

tab1, tab2 = st.tabs(["📤 Business: Submit HC / 提报新 HC", "✅ HR: Approve HC / 审批 HC 需求"])

with tab1:
    st.markdown("### HC Request Form / 业务线需求申请表")
    st.info(
        "🌐 **Language Note / 语言说明：** Supports Chinese or English input.\n\n"
        "- **English** input is saved directly and flows to downstream modules.\n"
        "- **Chinese** input will be **auto-translated to English** upon submission "
        "for optimal JD generation and X-Ray sourcing.\n\n"
        "- 如果您用**英文**填写，内容将直接保存并流转至后续模块。\n"
        "- 如果您用**中文**填写，系统提交时会**自动翻译成英文**再保存，"
        "确保 JD 生成和 X-Ray 寻源获得最佳效果。"
    )
    with st.form("hc_request_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            department = st.selectbox(bi("Department", "需求部门"), ["Cloud Native R&D / 云原生研发中心", "Global Delivery / 全球交付中心", "Overseas Presales / 海外售前团队"])
            role_title = st.text_input("Role Title（岗位名称）", placeholder="E.g.: Technical Service Manager — Singapore")
            location = st.text_input("Target Location（工作地点）", placeholder="E.g.: Singapore / Malaysia / Remote APAC")
        with col_b:
            urgency = st.select_slider(bi("Urgency", "紧急程度"), options=["🔥 Low priority", "🔥🔥 Normal", "🔥🔥🔥 Critical — project blocked on hire"])

        mission = st.text_area("1️⃣ The Mission — what must this person deliver in Year 1? *", placeholder="E.g.: Lead 2 enterprise OpenShift replacement projects for financial clients in Singapore; build a standardized English-language delivery runbook.", height=80)
        tech_stack = st.text_input("2️⃣ Required Tech Stack（必须技术，逗号分隔）*", placeholder="E.g.: Kubernetes, OpenShift, Docker, Terraform, CI/CD, Linux")
        deal_breakers = st.text_input("3️⃣ Deal Breakers — hard disqualifiers（红线）", placeholder="E.g.: No business-level English; unwilling to travel; no B2B enterprise experience")
        selling_point = st.text_input("4️⃣ Selling Point — why should top talent join?（核心卖点）", placeholder="E.g.: High-caliber APAC clients; cutting-edge cloud-native stack; uncapped performance compensation")

        submit_hc = st.form_submit_button(bi("🚀 Submit HC Request", "🚀 提交 HC 申请"), type="primary")
        if submit_hc:
            if not role_title or not mission or not tech_stack:
                st.error(bi("Please fill in all required (*) fields!", "请完整填写标有 * 的必填项！"))
            else:
                def _has_chinese(text):
                    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))

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
                    with st.spinner(bi("🌐 Chinese detected, auto-translating to English...", "🌐 检测到中文内容，正在自动翻译为英文...")):
                        translated = agent.translate_hc_fields(fields)
                    role_title    = translated.get("role_title", role_title)
                    location      = translated.get("location", location)
                    mission       = translated.get("mission", mission)
                    tech_stack    = translated.get("tech_stack", tech_stack)
                    deal_breakers = translated.get("deal_breakers", deal_breakers)
                    selling_point = translated.get("selling_point", selling_point)
                    st.success(bi("✅ Auto-translated to English. Saved content shown below:", "✅ 已自动翻译为英文，以下是翻译后保存的内容："))
                    with st.expander(bi("📄 View translation", "📄 查看翻译结果"), expanded=True):
                        st.markdown(f"**Mission:** {mission}")
                        st.markdown(f"**Deal Breakers:** {deal_breakers}")
                        st.markdown(f"**Selling Point:** {selling_point}")

                hc_mgr.submit_request(department, role_title, location, urgency, mission, tech_stack, deal_breakers, selling_point)
                st.success(bi("✅ HC request submitted! Awaiting HR BP approval.", "✅ HC 申请已提交！等待 HR BP 审批。"))

with tab2:
    st.markdown("### HR BP Approval Console / HR BP 审批工作台")
    requests = hc_mgr.get_all_requests()
    if not requests:
        st.info(bi("No HC requests at this time.", "当前没有任何 HC 申请。"))
    else:
        for req in requests:
            status_color = "#F59E0B" if req['status'] == "Pending" else ("#10B981" if req['status'] == "Approved" else "#EF4444")
            status_icon = "⏳ Pending / 待审批" if req['status'] == "Pending" else ("✅ Approved / 已批准" if req['status'] == "Approved" else "❌ Rejected / 已驳回")

            with st.expander(f"{req['date']} | {req['department']} - {req['role_title']} [{status_icon}]"):
                st.markdown(f"**Location / 地点**: {req['location']} &nbsp;&nbsp;|&nbsp;&nbsp; **Urgency / 紧急度**: {req['urgency']}")
                st.markdown(f"**Mission / 使命**: {req['mission']}")
                st.markdown(f"**Tech Stack / 技术栈**: {req['tech_stack']}")
                st.markdown(f"**Deal Breakers / 红线**: {req['deal_breakers']} &nbsp;&nbsp;|&nbsp;&nbsp; **Selling Point / 卖点**: {req['selling_point']}")

                if req['status'] == "Pending":
                    c1, c2 = st.columns([1, 10])
                    with c1:
                        if st.button(bi("Approve", "批准"), key=f"approve_{req['id']}", type="primary"):
                            hc_mgr.update_status(req['id'], "Approved")
                            st.rerun()
                    with c2:
                        if st.button(bi("Reject", "驳回"), key=f"reject_{req['id']}"):
                            hc_mgr.update_status(req['id'], "Rejected")
                            st.rerun()
