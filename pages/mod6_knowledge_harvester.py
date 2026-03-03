import html
import os

import requests
import streamlit as st
from bs4 import BeautifulSoup

from app_shared import bi, get_agent, _llm_cache_key
from knowledge_manager import KnowledgeManager

st.markdown('<div class="main-title">🏗️ Knowledge Auto-Harvester / 知识库全自动收割机</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">No more manual entry! Input authoritative policy URLs or competitor sites — AI crawls, cleans, and deposits structured knowledge.\n告别人工录入！只需输入权威政策网页或竞品招聘网址，AI 爬虫将自动提取、清洗并将其沉淀为结构化的本地知识库。</div>', unsafe_allow_html=True)

agent = get_agent(_key=_llm_cache_key())
km = KnowledgeManager()

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🕸️ Method 1: AI Web Auto-Crawl / AI 网页情报自动抓取")
    with st.form("auto_harvester_form", clear_on_submit=True):
        # 提供权威信息源快捷下拉填充
        official_urls = {
            "Custom input / 自定义输入 (paste URL below)": "",
            "🇸🇬 新加坡 EP 签证 COMPASS 计分制 (解析版)": "https://sg.acclime.com/guides/singapore-employment-pass/",
            "🇸🇬 新加坡 CPF (公积金) 费率政策 (普华永道解析)": "https://taxsummaries.pwc.com/singapore/individual/other-taxes",
            "🇲🇾 马来西亚最新劳工法修正案 (法律解析)": "https://www.taypartners.com.my/employment-act-1955-key-amendments-2023/",
            "🇲🇾 马来西亚外籍专才 EP 签证申请指南": "https://www.paulhypepage.my/guide/malaysia-employment-pass/",
            "🇭🇰 香港'高才通'与专才签证对比 (毕马威指南)": "https://www.pwccn.com/zh/services/tax/publications/tax-news-mar2024-1.html",
            "🇭🇰 香港雇佣条例与解雇规定 (Deacons)": "https://www.deacons.com/zh-hant/news-and-insights/publications/employment-law-in-hong-kong-frequently-asked-questions/",
            "🇿🇦 南非外籍关键技能签证 (Critical Skills) 解析": "https://www.xpatweb.com/south-africa-critical-skills-visa/",
            "🇿🇦 南非解雇与劳动法实务 (Bowmans)": "https://www.bowmanslaw.com/insights/employment/south-africa-terminating-employment/"
        }

        selected_preset = st.selectbox(bi("💡 Quick-select official source (auto-fill URL)", "💡 快速选择官方信息源 (自动填充链接)"), list(official_urls.keys()))
        default_url = official_urls[selected_preset]

        target_url = st.text_input(bi("🔗 Target URL", "🔗 目标网页 URL"), value=default_url, placeholder="Paste any webpage URL here / 在此处粘贴任何网页链接...")
        region = st.selectbox(bi("Region", "归属区域"), ["Singapore", "Malaysia", "South Africa", "Middle East", "Global/General"])
        category = st.selectbox(bi("Category", "情报分类"), ["Official Law / 官方政策法规", "Market Intel / 薪酬与竞品情报", "Visa & Work Permit / 签证与工作许可", "Other / 其他避雷指南"])

        submitted_url = st.form_submit_button(bi("🤖 Crawl & Extract Knowledge", "🤖 启动爬虫并提取知识"), type="primary")

        if submitted_url:
            if not target_url.strip() or not target_url.startswith("http"):
                st.error(bi("Please enter a valid URL (http:// or https://)", "请输入有效的网页链接（需包含 http:// 或 https://）"))
            else:
                if not os.getenv("OPENAI_API_KEY"):
                    st.error(bi("LLM API Key missing, cannot clean content.", "缺失大模型 API Key，无法进行内容清洗。"))
                else:
                    with st.spinner(bi(f"Crawling {target_url}...", f"正在爬取 {target_url} 的内容...")):
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.5'}
                            response = requests.get(target_url, headers=headers, timeout=10, verify=True)
                            response.raise_for_status()

                            soup = BeautifulSoup(response.text, 'html.parser')
                            for script in soup(["script", "style", "nav", "footer"]):
                                script.decompose()

                            raw_text = soup.get_text(separator=' ', strip=True)

                            if len(raw_text) < 50:
                                st.error(bi("Page appears to block crawlers or has too little content.", "该网页似乎限制了爬虫或内容过少，未能抓取到有效文本。"))
                            else:
                                st.success(bi(f"✅ Crawl successful ({len(raw_text)} chars). Passing to AI for extraction...", f"✅ 网页爬取成功（共 {len(raw_text)} 字符），正在交由 AI 进行知识萃取..."))

                                with st.spinner(bi("🤖 AI extracting core policy intelligence...", "🤖 AI 正在萃取核心政策情报...")):
                                    ai_result = agent.extract_web_knowledge(target_url, region, category, raw_text)

                                    if "EXTRACTION_FAILED" in ai_result:
                                        st.warning(bi("AI found no actionable intelligence on this page.", "AI 未能在该网页中找到有价值的情报。"))
                                    else:
                                        tags = f"{region}, Auto-Harvested, {category.split(' ')[0]}"
                                        _ok, _reason = km.add_fragment(region, category, ai_result, tags, source_url=target_url)
                                        if _ok:
                                            st.success(bi("🎉 Knowledge extracted & saved to database!", "🎉 知识萃取成功！已自动存入底层数据库。"))
                                            st.info(bi("Extracted key content below:\n", "提取到的精华内容如下：\n") + ai_result)
                                        else:
                                            st.warning(bi("⚠️ Duplicate content detected — skipped (dedup protection).", "⚠️ 该内容与已有条目重复，已跳过（去重保护）。"))
                        except Exception as e:
                            st.error(bi(f"Crawl error: {str(e)}", f"抓取网页时发生错误: {str(e)}"))

    st.markdown("---")
    st.markdown("### 📝 Method 2: Manual Entry / 人工补充 (备用)")
    with st.expander(bi("Click to expand manual entry panel", "点击展开手工录入面板")):
        with st.form("manual_fragment_form", clear_on_submit=True):
            man_region = st.selectbox(bi("Region", "区域"), ["Singapore", "Malaysia", "South Africa", "Hong Kong", "Global/General"])
            man_category = st.selectbox(bi("Category", "分类"), ["Compensation & Benefits / 薪酬福利", "Visa & Compliance / 签证与合规", "Local Recruiter Insights / 本地猎头潜规则"])
            man_content = st.text_area(bi("Content", "具体经验"), height=100)
            if st.form_submit_button(bi("Save", "保存")):
                if man_content.strip():
                    _ok, _reason = km.add_fragment(man_region, man_category, man_content, "Manual")
                    if _ok:
                        st.success(bi("Saved successfully", "录入成功"))
                    else:
                        st.warning(bi("⚠️ Duplicate content, skipped.", "⚠️ 该内容与已有条目重复，已跳过。"))

with col2:
    st.markdown("### 🗂️ Knowledge Compilation Center / 知识库编译中心")
    st.info(bi("All harvested intelligence (AI or manual) must be compiled before the RAG engine can access it. Click below.", "无论是 AI 网页爬虫还是人工录入获取的情报，都需要点击下方按钮进行统一编译。编译后，RAG 大脑才能读取到这些最新知识。"))

    if st.button(bi("🚀 Compile Playbook & Sync to RAG", "🚀 编译 Playbook 并同步至 RAG 引擎"), type="primary", use_container_width=True):
        with st.spinner(bi("Compiling fragments into structured Markdown...", "正在将零散情报汇编为结构化 Markdown 库...")):
            success = km.compile_to_markdown()
            if success:
                from document_parser import invalidate_rag_index
                invalidate_rag_index()
                st.success(bi("✅ Dynamic Playbook compiled! RAG engine refreshed — new knowledge active.", "✅ 动态 Playbook 编译完成！RAG 引擎已自动刷新，新知识立即生效。"))
                st.info(bi("💡 You can now ask questions in Module 5 — no restart needed.", "💡 现在可直接前往【模块五】提问，无需重启系统。"))
            else:
                st.warning(bi("No intelligence in the database yet.", "目前数据库中没有任何情报。"))

    st.markdown("---")
    fragments = km.get_all_fragments()
    if not fragments:
        st.info(bi("Knowledge base is empty. Enter URLs on the left for AI to harvest.", "知识情报库目前为空。请在左侧输入网址让 AI 去收割。"))
    else:
        _expired_count = sum(1 for f in fragments if km.get_expiry_status(f) == "expired")
        _soon_count = sum(1 for f in fragments if km.get_expiry_status(f) == "expiring_soon")
        if _expired_count:
            st.error(bi(f"⚠️ {_expired_count} item(s) expired (>90 days) — recommend re-crawling.", f"⚠️ {_expired_count} 条情报已过期（超过 90 天）— 建议重新爬取更新。"))
        if _soon_count:
            st.warning(bi(f"🕐 {_soon_count} item(s) expiring within 14 days — update soon.", f"🕐 {_soon_count} 条情报将在 14 天内过期，请留意及时更新。"))
        st.write(bi(f"**{len(fragments)}** high-value intelligence items in database:", f"当前库中共有 **{len(fragments)}** 条高价值情报："))
        with st.container(height=450):
            for f in fragments:
                _status = km.get_expiry_status(f)
                _border_color = "#DC2626" if _status == "expired" else ("#F59E0B" if _status == "expiring_soon" else "#004D99")
                _exp_label = f" · <span style='color:{_border_color};font-size:0.75em;'>{'⚠️ Expired / 已过期' if _status == 'expired' else ('🕐 Expiring soon / 即将过期 ' + f.get('expires_at','') if _status == 'expiring_soon' else 'Valid until / 有效至 ' + f.get('expires_at',''))}</span>"
                st.markdown(f"""
                <div style="background-color: #FFFFFF; padding: 15px; border-radius: 6px; border: 1px solid #E2E8F0; margin-bottom: 10px; border-left: 3px solid {_border_color};">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong>{html.escape(f['region'])} - {html.escape(f['category'])}</strong>
                        <span style="color: #6B7280; font-size: 0.8em;">{html.escape(f['date'])}{_exp_label}</span>
                    </div>
                    <p style="color: #4B5563; font-size: 0.9em; margin: 0;">{html.escape(f['content'])}</p>
                </div>
                """, unsafe_allow_html=True)
