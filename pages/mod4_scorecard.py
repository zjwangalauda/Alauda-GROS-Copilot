import html
import os

import streamlit as st

from app_shared import get_agent, load_latest_jd

st.markdown('<div class="main-title">📝 结构化面试评估系统</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">消除面试过程中的主观偏见。基于 JD 自动提取关键维度，生成【行为锚定评分卡 (Scorecard)】与【STAR 题库】。</div>', unsafe_allow_html=True)

agent = get_agent()

default_jd_text, jd_msg = load_latest_jd()
if default_jd_text and jd_msg:
    st.info(jd_msg)
elif not default_jd_text:
    st.warning("No JD found. Recommend generating one in Module 1 first, or paste an English JD below.")

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
            st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E7EB;">{html.escape(scorecard_result)}</div>', unsafe_allow_html=True)

            if scorecard_result:
                st.download_button(
                    label="📥 下载评估表单 (Markdown)",
                    data=scorecard_result,
                    file_name="Alauda_Interview_Scorecard.md",
                    mime="text/markdown",
                )
