import os
import streamlit as st

st.markdown('<div class="main-title">🌍 灵雀云全球精英招聘指挥中心</div>', unsafe_allow_html=True)

# --- Temporary diagnostic (remove after debugging) ---
with st.expander("🔧 LLM 连接诊断 (点击展开)"):
    if st.button("运行诊断"):
        key = os.environ.get("OPENAI_API_KEY", "")
        base = os.environ.get("OPENAI_API_BASE", "")
        model = os.environ.get("LLM_MODEL", "")
        strong = os.environ.get("STRONG_MODEL", "")

        st.write(f"**OPENAI_API_KEY**: `{key[:8]}...{key[-4:]}`" if len(key) > 12 else f"**OPENAI_API_KEY**: `{key or '(empty)'}`")
        st.write(f"**OPENAI_API_BASE**: `{base or '(empty)'}`")
        st.write(f"**LLM_MODEL**: `{model or '(empty)'}`")
        st.write(f"**STRONG_MODEL**: `{strong or '(empty)'}`")

        if key and base:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=key, base_url=base)
                resp = client.chat.completions.create(
                    model=strong or model or "claude-opus-4-6",
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5,
                )
                st.success(f"API call OK! Response: {resp.choices[0].message.content}")
            except Exception as e:
                st.error(f"API call failed: {e}")
        else:
            st.warning("API key or base URL is empty — secrets not loaded properly.")
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
