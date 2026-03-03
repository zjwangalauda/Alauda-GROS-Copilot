import html
import os

import streamlit as st

from app_shared import bi, get_agent, load_latest_jd, _llm_cache_key

st.markdown('<div class="main-title">✉️ High-Conversion Cold Outreach / 高转化率自动化触达</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Ditch generic HR pitches. Generate laser-targeted, highly personalized headhunter-grade Email &amp; LinkedIn InMail.\n抛弃"我们在招人，你有兴趣吗"的废话，一键生成直击痛点、高度个性化的猎头级触达邮件与 LinkedIn InMail。</div>', unsafe_allow_html=True)

agent = get_agent(_key=_llm_cache_key())

default_jd_text, jd_msg = load_latest_jd()
if default_jd_text and jd_msg:
    st.info(jd_msg)
elif not default_jd_text:
    st.warning(bi("Recommend generating a JD in Module 1 first, or paste JD below.", "建议先去【模块一】生成职位描述，或者在下方手动粘贴 JD 核心信息。"))

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

    submitted = st.form_submit_button(bi("✉️ Generate Outreach (Email & InMail)", "✉️ 生成触达话术"), type="primary", use_container_width=True)

if submitted:
    if not os.getenv("OPENAI_API_KEY"):
        st.error(bi("LLM API Key not configured.", "您尚未配置大模型 API Key。"))
    else:
        with st.spinner(bi("🤖 Applying Hormozi's Acquisition framework to craft copy...", "🤖 正在运用 Hormozi Acquisition 营销框架构思文案...")):
            candidate_info = f"姓名: {candidate_name}\n背景亮点: {candidate_bg}"
            outreach_result = agent.generate_outreach_message(jd_input, candidate_info)

            st.success(bi("✅ Outreach copy generated! Ready to copy & send.", "✅ 触达文案生成完毕！可直接复制发送。"))
            st.markdown(f'<div style="background-color: #FFFFFF; padding: 30px; border-radius: 8px; border: 1px solid #E5E7EB;">{html.escape(outreach_result)}</div>', unsafe_allow_html=True)
