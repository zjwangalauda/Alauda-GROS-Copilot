import streamlit as st

from app_shared import get_agent, get_rag_system, _llm_cache_key, _emb_cache_key

st.markdown('<div class="main-title">📚 灵雀云出海智库 AI 助手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">基于 RAG 检索增强技术。您可以随时询问关于本地化合规、出海战略指导手册、雇主品牌沟通话术等内容。</div>', unsafe_allow_html=True)

agent = get_agent(_key=_llm_cache_key())
rag = get_rag_system(_key=_emb_cache_key())

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
