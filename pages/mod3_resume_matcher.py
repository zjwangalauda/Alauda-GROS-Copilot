import html
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from app_shared import get_agent, load_latest_jd, _llm_cache_key

st.markdown('<div class="main-title">📄 猎头简历智能雷达 (Resume Matcher)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">解决 HR 看不懂海外技术简历、容易被候选人过度包装忽悠的问题。AI 基于严苛的【算分卡法则】进行防漂移量化打分。</div>', unsafe_allow_html=True)

agent = get_agent(_key=_llm_cache_key())

# 左右两栏布局：左边 JD，右边简历上传
col_jd, col_resume = st.columns([1, 1])

with col_jd:
    st.markdown("### 🎯 Benchmark: Job Description")
    default_jd_for_match, jd_msg = load_latest_jd()
    if default_jd_for_match and jd_msg:
        st.info(jd_msg)
    elif not default_jd_for_match:
        st.warning("Recommend generating a JD in Module 1 first, or paste an English JD below.")
    st.caption("🇬🇧 Use an English JD for best results — the scoring rubric and resume comparison both perform better in a single language.")
    jd_for_match = st.text_area("Paste or edit JD content", value=default_jd_for_match, height=350, key="resume_jd_input")

with col_resume:
    st.markdown("### 📤 批量上传候选人简历")
    uploaded_resumes = st.file_uploader(
        "支持 PDF / TXT 格式，可同时上传多份",
        type=["pdf", "docx", "txt"],
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

        # Phase 1 (serial): parse all uploaded files
        parsed = []
        for resume_file in uploaded_resumes:
            file_bytes = resume_file.read()
            file_name = resume_file.name
            resume_text = agent.extract_text_from_file(file_name, file_bytes)
            parsed.append((file_name, resume_text))

        # Phase 2 (parallel): evaluate resumes concurrently
        progress_bar = st.progress(0, text="🤖 正在并行评估简历...")
        results = {}  # idx -> result string
        error_indices = set()

        def _evaluate(idx, name, text):
            return idx, agent.evaluate_resume(jd_for_match, text)

        completed_count = 0
        total = len(parsed)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for idx, (file_name, resume_text) in enumerate(parsed):
                if resume_text.startswith("File parsing failed") or resume_text.startswith("Unsupported file format"):
                    error_indices.add(idx)
                    results[idx] = resume_text
                    completed_count += 1
                    continue
                fut = executor.submit(_evaluate, idx, file_name, resume_text)
                futures[fut] = idx

            for fut in as_completed(futures):
                try:
                    idx, result = fut.result()
                    results[idx] = result
                except Exception as e:
                    idx = futures[fut]
                    results[idx] = f"❌ Evaluation failed: {str(e)}"
                    error_indices.add(idx)
                completed_count += 1
                progress_bar.progress(completed_count / total, text=f"🤖 已完成 {completed_count}/{total} 份简历评估")

        progress_bar.empty()

        # Phase 3 (serial): display results in original upload order
        for idx, (file_name, _) in enumerate(parsed):
            if idx in error_indices:
                st.error(f"❌ {file_name}: {results[idx]}")
                continue
            with st.expander(f"📄 {file_name}", expanded=True):
                st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E7EB;">{html.escape(results[idx])}</div>', unsafe_allow_html=True)

        st.success(f"✅ 全部 {len(uploaded_resumes)} 份简历评估完毕！")
