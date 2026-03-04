"""M8: Auto Sourcing — Talent Pool + Automated Matching + Shortlist Management."""

import html
from datetime import datetime, timedelta

import streamlit as st

from app_shared import bi, get_agent, _llm_cache_key
from auto_sourcer import AutoSourcer, FREEZE_DAYS, PASS_THRESHOLD
from hc_manager import HCManager
from talent_pool_manager import TalentPoolManager

st.markdown(
    '<div class="main-title">🤖 Auto Sourcing / 自动寻源</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">'
    "Automated talent pool scanning, AI-powered resume scoring, and shortlist management.\n"
    "自动扫描简历库，AI 智能评分，生成推荐清单并跟踪候选人意向"
    "</div>",
    unsafe_allow_html=True,
)

agent = get_agent(_llm_cache_key())
tpm = TalentPoolManager()
sourcer = AutoSourcer(agent)
hm = HCManager()

# =====================================================================
# Tabs
# =====================================================================
tab_pool, tab_run, tab_shortlist, tab_frozen = st.tabs([
    bi("📁 Talent Pool", "📁 简历库"),
    bi("⚡ Auto Sourcing", "⚡ 自动寻源"),
    bi("📋 Shortlist", "📋 推荐清单"),
    bi("🧊 Frozen", "🧊 冷冻名单"),
])

# =====================================================================
# Tab 1: Talent Pool
# =====================================================================
with tab_pool:
    # Stats banner
    pool_stats = tpm.get_stats()
    _sc1, _sc2 = st.columns(2)
    with _sc1:
        st.metric(bi("Total Resumes", "简历总数"), pool_stats["total"])
    with _sc2:
        st.metric(bi("Added This Week", "本周新增"), pool_stats["recent_7d"])

    st.markdown("---")

    # Upload section
    st.markdown(f"### {bi('Upload Resumes', '上传简历')}")
    uploaded_files = st.file_uploader(
        bi("Drop resume files here (PDF, DOCX, TXT)", "拖入简历文件（PDF、DOCX、TXT）"),
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="talent_pool_uploader",
    )
    if uploaded_files:
        if st.button(bi("📥 Import to Talent Pool", "📥 导入简历库"), type="primary"):
            with st.spinner(bi("Parsing and importing...", "正在解析和导入...")):
                result = tpm.import_files(uploaded_files, agent)
            st.success(
                bi(
                    f"Imported: {result['imported']}, Duplicates skipped: {result['skipped_dup']}, "
                    f"Unsupported: {result['skipped_unsupported']}",
                    f"已导入: {result['imported']}，重复跳过: {result['skipped_dup']}，"
                    f"不支持格式: {result['skipped_unsupported']}",
                )
            )
            if result["errors"]:
                for err in result["errors"]:
                    st.error(err)
            st.rerun()

    # Directory scan
    with st.expander(bi("📂 Import from Directory", "📂 从目录导入")):
        dir_path = st.text_input(
            bi("Directory path", "目录路径"),
            placeholder="/path/to/resumes/",
        )
        if st.button(bi("Scan & Import", "扫描并导入")) and dir_path.strip():
            with st.spinner(bi("Scanning directory...", "正在扫描目录...")):
                result = tpm.import_from_directory(dir_path.strip(), agent)
            st.success(
                bi(
                    f"Imported: {result['imported']}, Duplicates: {result['skipped_dup']}",
                    f"已导入: {result['imported']}，重复: {result['skipped_dup']}",
                )
            )
            if result["errors"]:
                for err in result["errors"]:
                    st.error(err)
            st.rerun()

    # Talent list with evaluation status
    st.markdown(f"### {bi('Resume Library', '简历库列表')}")
    all_talents = tpm.get_all_with_eval_status()
    if not all_talents:
        st.info(bi("No resumes in the talent pool yet.", "简历库暂无数据，请上传简历。"))
    else:
        for t in all_talents:
            # Evaluation status badge
            _eval_badge_text = ""
            if t.get("best_score") is not None:
                _bs = t["best_score"]
                if _bs >= 80:
                    _eval_badge_text = f"Best: {_bs:.0f}/100 Strong Match"
                elif _bs >= 60:
                    _eval_badge_text = f"Best: {_bs:.0f}/100 Borderline"
                else:
                    _eval_badge_text = f"Best: {_bs:.0f}/100 Disqualified"
            else:
                _eval_badge_text = "Not Screened"

            _tags_str = ""
            if t.get("tags"):
                _tags_str = " · ".join(tag.strip() for tag in t["tags"].split(",")[:6])

            _display_name = t.get("candidate_name") or t["file_name"]
            _expander_label = f"{_display_name}  |  {_eval_badge_text}  |  {t['uploaded_at']}"

            with st.expander(_expander_label, expanded=False):
                # --- Contact & file info ---
                _info_col, _action_col = st.columns([4, 1])
                with _info_col:
                    st.markdown(f"**{bi('File', '文件')}:** {html.escape(t['file_name'])}")
                    if t.get("email"):
                        st.markdown(f"**Email:** {html.escape(t['email'])}")
                    if t.get("phone"):
                        st.markdown(f"**{bi('Phone', '电话')}:** {html.escape(t['phone'])}")
                    if t.get("linkedin_url"):
                        st.markdown(f"**LinkedIn:** [{html.escape(t['linkedin_url'])}]({t['linkedin_url']})")
                    if _tags_str:
                        st.markdown(f"**{bi('Skills', '技能')}:** {html.escape(_tags_str)}")
                    st.markdown(f"**{bi('Uploaded', '上传日期')}:** {html.escape(t['uploaded_at'])}")
                with _action_col:
                    if st.button(bi("Delete", "删除"), key=f"del_{t['id']}", use_container_width=True, type="secondary"):
                        st.session_state[f"confirm_del_{t['id']}"] = True
                if st.session_state.get(f"confirm_del_{t['id']}"):
                    st.warning(bi(
                        f"Delete {_display_name}? This also removes related shortlist entries.",
                        f"确认删除 {_display_name}？相关的推荐清单记录也会被移除。",
                    ))
                    _dc1, _dc2 = st.columns(2)
                    with _dc1:
                        if st.button(bi("Confirm Delete", "确认删除"), key=f"cfm_del_{t['id']}", type="primary", use_container_width=True):
                            tpm.delete_talent(t["id"])
                            st.session_state.pop(f"confirm_del_{t['id']}", None)
                            st.rerun()
                    with _dc2:
                        if st.button(bi("Cancel", "取消"), key=f"cancel_del_{t['id']}", use_container_width=True):
                            st.session_state.pop(f"confirm_del_{t['id']}", None)
                            st.rerun()

                # --- Resume text ---
                st.markdown(f"#### {bi('Resume Content', '简历内容')}")
                _parsed = t.get("parsed_text") or ""
                if _parsed:
                    st.text_area(
                        bi("Parsed text", "解析文本"),
                        value=_parsed,
                        height=200,
                        disabled=True,
                        key=f"resume_{t['id']}",
                        label_visibility="collapsed",
                    )
                else:
                    st.info(bi("No parsed text available.", "暂无解析文本。"))

                # --- Evaluation details ---
                _evals = sourcer.get_evaluations_for_talent(t["id"])
                if _evals:
                    st.markdown(f"#### {bi('Screening Results', '筛选评分明细')}  ({len(_evals)} HC)")
                    for _ev in _evals:
                        _ev_score = _ev.get("score", 0)
                        _sc_color = "#10B981" if _ev_score >= 80 else "#F59E0B" if _ev_score >= 60 else "#DC2626"
                        _ev_verdict = _ev.get("verdict", "")
                        _ev_disp = _ev.get("disposition", "Pending")
                        st.markdown(
                            f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-left:4px solid {_sc_color};"
                            f"border-radius:6px;padding:10px 14px;margin-bottom:6px;'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                            f"<span style='font-weight:600;'>{html.escape(_ev.get('role_title', ''))}"
                            f" · {html.escape(_ev.get('hc_location', ''))}</span>"
                            f"<span style='font-size:1.1rem;font-weight:700;color:{_sc_color};'>{_ev_score:.0f}/100</span></div>"
                            f"<div style='color:#64748B;font-size:0.8rem;margin-top:2px;'>"
                            f"Verdict: {html.escape(_ev_verdict)} · Status: {html.escape(_ev_disp)}"
                            f" · {html.escape(_ev.get('created_at', ''))}</div></div>",
                            unsafe_allow_html=True,
                        )
                        with st.expander(bi("View Full Evaluation", "查看完整评估"), expanded=False):
                            st.markdown(_ev.get("evaluation_md") or bi("No detail.", "暂无详情。"))
                else:
                    st.markdown(f"#### {bi('Screening Results', '筛选评分明细')}")
                    st.info(bi(
                        "Not screened yet. Run Auto Sourcing in Tab 2 to evaluate.",
                        "尚未筛选。请在「自动寻源」标签页运行扫描。",
                    ))

# =====================================================================
# Tab 2: Auto Sourcing Runs
# =====================================================================
with tab_run:
    st.markdown(f"### {bi('Run Auto Sourcing', '运行自动寻源')}")

    _approved_hcs = hm.get_approved_requests()
    _all_talents = tpm.get_all_talents()
    st.markdown(
        bi(
            f"**Ready:** {len(_approved_hcs)} approved HC(s), {len(_all_talents)} resume(s) in pool.",
            f"**就绪：** {len(_approved_hcs)} 个已审批HC，简历库中 {len(_all_talents)} 份简历。",
        )
    )

    _rc1, _rc2 = st.columns(2)
    with _rc1:
        if st.button(
            bi("🚀 Run Incremental Scan", "🚀 运行增量扫描"),
            type="primary",
            use_container_width=True,
            disabled=(not _approved_hcs or not _all_talents),
        ):
            with st.spinner(bi("Running auto sourcing (incremental)...", "正在运行自动寻源（增量）...")):
                run_id = sourcer.run(force_full=False)
            _run = next((r for r in sourcer.get_run_history() if r["id"] == run_id), None)
            if _run:
                st.success(
                    bi(
                        f"Completed! Scanned {_run['talent_scanned']} resumes, found {_run['matches_found']} matches "
                        f"(≥{PASS_THRESHOLD}pts) in {_run['duration_seconds']}s.",
                        f"完成！扫描 {_run['talent_scanned']} 份简历，找到 {_run['matches_found']} 个匹配"
                        f"（≥{PASS_THRESHOLD}分），耗时 {_run['duration_seconds']}秒。",
                    )
                )
            st.rerun()
    with _rc2:
        if st.button(
            bi("🔄 Run Full Scan", "🔄 运行全量扫描"),
            use_container_width=True,
            disabled=(not _approved_hcs or not _all_talents),
        ):
            with st.spinner(bi("Running auto sourcing (full)...", "正在运行自动寻源（全量）...")):
                run_id = sourcer.run(force_full=True)
            _run = next((r for r in sourcer.get_run_history() if r["id"] == run_id), None)
            if _run:
                st.success(
                    bi(
                        f"Completed! Scanned {_run['talent_scanned']} resumes, found {_run['matches_found']} matches.",
                        f"完成！扫描 {_run['talent_scanned']} 份简历，找到 {_run['matches_found']} 个匹配。",
                    )
                )
            st.rerun()

    # Run history
    st.markdown(f"### {bi('Run History', '运行历史')}")
    _runs = sourcer.get_run_history()
    if not _runs:
        st.info(bi("No sourcing runs yet.", "暂无运行记录。"))
    else:
        for _r in _runs[:20]:
            _status_color = {"completed": "#10B981", "running": "#F59E0B", "failed": "#DC2626"}.get(_r["status"], "#64748B")
            st.markdown(
                f"<div style='background:#fff;border:1px solid #E2E8F0;border-left:4px solid {_status_color};"
                f"border-radius:6px;padding:10px 14px;margin-bottom:4px;'>"
                f"<div style='display:flex;justify-content:space-between;'>"
                f"<span style='font-weight:600;'>{html.escape(_r['run_date'])}</span>"
                f"<span style='background:{'#DCFCE7' if _r['run_type']=='incremental' else '#DBEAFE'};"
                f"color:{'#166534' if _r['run_type']=='incremental' else '#1E40AF'};"
                f"padding:2px 8px;border-radius:10px;font-size:0.72rem;'>{_r['run_type']}</span></div>"
                f"<div style='color:#64748B;font-size:0.82rem;margin-top:4px;'>"
                f"HC: {_r['hc_count']} · Scanned: {_r['talent_scanned']} · "
                f"Matches: {_r['matches_found']} · {_r['duration_seconds']}s</div></div>",
                unsafe_allow_html=True,
            )

    # Cron setup instructions
    with st.expander(bi("⏰ Schedule Weekly Runs (Cron)", "⏰ 设置每周定时运行（Cron）")):
        st.code(
            "# Run every Sunday at 2:00 AM\n"
            "0 2 * * 0 cd /path/to/Recruitment && python run_auto_sourcing.py >> logs/auto_sourcing.log 2>&1\n\n"
            "# Force full scan on first Sunday of month\n"
            "0 2 1-7 * 0 cd /path/to/Recruitment && python run_auto_sourcing.py --full >> logs/auto_sourcing.log 2>&1",
            language="bash",
        )

# =====================================================================
# Tab 3: Shortlist
# =====================================================================
with tab_shortlist:
    st.markdown(f"### {bi('Screening Results', '筛选结果清单')}")

    # Filters
    _fc1, _fc2, _fc3 = st.columns(3)
    with _fc1:
        _hc_options = ["All / 全部"] + [f"{h['id']} — {h['role_title']} ({h['location']})" for h in _approved_hcs]
        _selected_hc_label = st.selectbox(bi("Filter by HC", "按HC筛选"), _hc_options)
        _filter_hc = None if _selected_hc_label == "All / 全部" else _selected_hc_label.split(" — ")[0]
    with _fc2:
        _qual_options = [
            bi("Qualified (>=60)", "合格 (>=60分)"),
            bi("Disqualified (<60)", "不合格 (<60分)"),
            "All / 全部",
        ]
        _selected_qual = st.selectbox(bi("Filter by Score", "按评分筛选"), _qual_options)
        _filter_qual = "qualified" if "Qualified" in _selected_qual else "disqualified" if "Disqualified" in _selected_qual else None
    with _fc3:
        _disp_options = ["Pending", "Interested", "Not Interested", "All / 全部"]
        _selected_disp = st.selectbox(bi("Filter by Status", "按状态筛选"), _disp_options)
        _filter_disp = None if _selected_disp == "All / 全部" else _selected_disp

    shortlist = sourcer.get_shortlist(hc_id=_filter_hc, disposition=_filter_disp, qualified=_filter_qual)

    if not shortlist:
        st.info(bi(
            "No matching candidates found. Run auto sourcing first or adjust filters.",
            "未找到匹配候选人。请先运行自动寻源或调整筛选条件。",
        ))
    else:
        # Summary counts
        _qualified_count = sum(1 for s in shortlist if s.get("score", 0) >= PASS_THRESHOLD)
        _disqualified_count = len(shortlist) - _qualified_count
        st.markdown(
            bi(
                f"**{len(shortlist)} candidate(s)** — Qualified: {_qualified_count}, Disqualified: {_disqualified_count}",
                f"**共 {len(shortlist)} 名候选人** — 合格: {_qualified_count}，不合格: {_disqualified_count}",
            )
        )

        for idx, sl in enumerate(shortlist):
            _score = sl.get("score", 0)
            _is_qualified = _score >= PASS_THRESHOLD
            _score_color = "#10B981" if _score >= 80 else "#F59E0B" if _score >= 60 else "#DC2626"
            _verdict = sl.get("verdict", "")
            _disp = sl.get("disposition", "Pending")

            # Build status badges
            _badges = ""
            if not _is_qualified:
                _badges += '<span style="background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:10px;font-size:0.72rem;margin-right:4px;">Disqualified</span>'
            _disp_badge = {
                "Pending": '<span style="background:#FEF3C7;color:#92400E;padding:2px 8px;border-radius:10px;font-size:0.72rem;">Pending</span>',
                "Interested": '<span style="background:#DCFCE7;color:#166534;padding:2px 8px;border-radius:10px;font-size:0.72rem;">Interested</span>',
                "Not Interested": '<span style="background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:10px;font-size:0.72rem;">Frozen</span>',
            }.get(_disp, "")
            _badges += _disp_badge

            _bg_color = "#fff" if _is_qualified else "#FAFAFA"
            st.markdown(
                f"<div style='background:{_bg_color};border:1px solid #E2E8F0;border-left:4px solid {_score_color};"
                f"border-radius:8px;padding:14px 16px;margin-bottom:8px;"
                f"{'opacity:0.7;' if not _is_qualified else ''}'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<div>"
                f"<span style='font-weight:700;font-size:1rem;'>{html.escape(sl.get('candidate_name') or 'Unknown')}</span> "
                f"{_badges}"
                f"</div>"
                f"<div style='font-size:1.2rem;font-weight:700;color:{_score_color};'>{_score:.0f}/100</div></div>"
                f"<div style='color:#64748B;font-size:0.82rem;margin-top:4px;'>"
                f"HC: {html.escape(sl.get('role_title', ''))} · {html.escape(sl.get('hc_location', ''))}"
                f"{' · ' + html.escape(sl.get('email', '')) if sl.get('email') else ''}"
                f"{' · LinkedIn' if sl.get('talent_linkedin') else ''}"
                f"</div>"
                f"<div style='color:#94A3B8;font-size:0.78rem;margin-top:2px;'>Verdict: {html.escape(_verdict)}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Action buttons — only for qualified & Pending candidates
            if _is_qualified and _disp == "Pending":
                _ac1, _ac2, _ac3 = st.columns([1, 1, 2])
                with _ac1:
                    if st.button(
                        bi("Interested", "有意愿"),
                        key=f"int_{sl['id']}_{idx}",
                        use_container_width=True,
                        type="primary",
                    ):
                        cand_id = sourcer.convert_to_candidate(sl["id"])
                        if cand_id:
                            st.success(bi(
                                f"Converted to pipeline candidate ({cand_id}).",
                                f"已转入主管线（{cand_id}）。",
                            ))
                            st.rerun()
                with _ac2:
                    if st.button(
                        bi("Not Interested", "无意愿"),
                        key=f"noint_{sl['id']}_{idx}",
                        use_container_width=True,
                    ):
                        st.session_state[f"show_freeze_{sl['id']}"] = True
                with _ac3:
                    pass

                # Freeze reason input
                if st.session_state.get(f"show_freeze_{sl['id']}"):
                    _freeze_note = st.text_input(
                        bi("Reason (optional)", "原因（可选）"),
                        key=f"freeze_note_{sl['id']}_{idx}",
                        placeholder=bi("e.g. Candidate not looking to move", "如：候选人暂无跳槽意向"),
                    )
                    if st.button(bi("Confirm Freeze", "确认冷冻"), key=f"cfm_freeze_{sl['id']}_{idx}"):
                        sourcer.set_disposition(sl["id"], "Not Interested", note=_freeze_note)
                        st.session_state.pop(f"show_freeze_{sl['id']}", None)
                        st.success(bi(
                            f"Frozen for {FREEZE_DAYS} days.",
                            f"已冷冻 {FREEZE_DAYS} 天。",
                        ))
                        st.rerun()

            # Expandable evaluation detail — available for both qualified and disqualified
            with st.expander(bi("View Full Evaluation", "查看完整评估"), expanded=False):
                st.markdown(sl.get("evaluation_md", "No evaluation data."))

# =====================================================================
# Tab 4: Frozen List
# =====================================================================
with tab_frozen:
    st.markdown(f"### {bi('Frozen Candidates', '冷冻候选人名单')}")
    st.markdown(
        bi(
            f"Candidates marked 'Not Interested' are frozen for {FREEZE_DAYS} days and excluded from future scans.",
            f"标记为'无意愿'的候选人将被冷冻 {FREEZE_DAYS} 天，期间不会在后续扫描中再次推荐。",
        )
    )

    frozen = sourcer.get_frozen_list()
    if not frozen:
        st.info(bi("No frozen candidates.", "暂无冷冻候选人。"))
    else:
        for idx, fr in enumerate(frozen):
            _disp_date = fr.get("disposition_date", "")
            _days_left = 0
            if _disp_date:
                try:
                    _frozen_until = datetime.strptime(_disp_date, "%Y-%m-%d") + timedelta(days=FREEZE_DAYS)
                    _days_left = max(0, (_frozen_until - datetime.now()).days)
                except ValueError:
                    pass

            st.markdown(
                f"<div style='background:#fff;border:1px solid #E2E8F0;border-left:4px solid #93C5FD;"
                f"border-radius:8px;padding:12px 16px;margin-bottom:6px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-weight:600;'>{html.escape(fr.get('candidate_name', 'Unknown'))}</span>"
                f"<span style='background:#DBEAFE;color:#1E40AF;padding:2px 8px;border-radius:10px;font-size:0.72rem;'>"
                f"❄️ {_days_left}d remaining</span></div>"
                f"<div style='color:#64748B;font-size:0.82rem;margin-top:4px;'>"
                f"📌 {html.escape(fr.get('role_title', ''))} · Frozen: {html.escape(_disp_date)}"
                f"{' · Reason: ' + html.escape(fr.get('disposition_note', '')) if fr.get('disposition_note') else ''}"
                f"</div></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                bi("🔓 Unfreeze", "🔓 解除冷冻"),
                key=f"unfreeze_{fr['id']}_{idx}",
            ):
                sourcer.unfreeze(fr["id"])
                st.success(bi("Unfrozen — will be included in next scan.", "已解冻，将在下次扫描中重新评估。"))
                st.rerun()
