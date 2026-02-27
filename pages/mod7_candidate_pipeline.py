import html

import streamlit as st

from candidate_manager import CandidateManager, PIPELINE_STAGES, STAGE_COLORS
from hc_manager import HCManager

st.markdown('<div class="main-title">👥 候选人 Pipeline 看板</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">追踪每位候选人在招聘漏斗中的实时状态，从寻源到入职全程可视化</div>', unsafe_allow_html=True)

cm = CandidateManager()

# --- 顶部统计 ---
stats = cm.get_stats()
_active_stages = ["Sourced", "Contacted", "Phone Screen", "Interview", "Offer"]
_active_count = sum(stats[s] for s in _active_stages)
_hired = stats.get("Hired", 0)
_total = len(cm.get_all())
_m7cols = st.columns(len(PIPELINE_STAGES))
for _i, _stage in enumerate(PIPELINE_STAGES):
    with _m7cols[_i]:
        _color = STAGE_COLORS[_stage]
        st.markdown(
            f"<div style='text-align:center;background:#fff;border:1px solid #E2E8F0;"
            f"border-top:3px solid {_color};border-radius:8px;padding:12px 4px;'>"
            f"<div style='font-size:1.5rem;font-weight:700;color:{_color};'>{stats[_stage]}</div>"
            f"<div style='font-size:0.78rem;color:#64748B;'>{_stage}</div></div>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# --- 新增候选人表单 ---
with st.expander("➕ 添加新候选人", expanded=(_total == 0)):
    _hc_ids = ["(不关联)"] + [r["id"] for r in HCManager().get_all_requests()]
    with st.form("add_candidate_form", clear_on_submit=True):
        _c1, _c2 = st.columns(2)
        with _c1:
            _cand_name = st.text_input("候选人姓名 *", placeholder="e.g. Zhang Wei")
            _cand_role = st.text_input("目标岗位 *", placeholder="e.g. Technical Service Manager")
            _cand_source = st.selectbox("来源渠道", ["LinkedIn X-Ray", "GitHub", "Referral", "Job Board", "Other"])
        with _c2:
            _cand_hc = st.selectbox("关联 HC 需求", _hc_ids)
            _cand_linkedin = st.text_input("LinkedIn / 个人主页", placeholder="https://linkedin.com/in/...")
            _cand_notes = st.text_area("备注", height=70, placeholder="初步印象、来源渠道细节...")
        if st.form_submit_button("✅ 加入 Pipeline", type="primary"):
            if _cand_name.strip() and _cand_role.strip():
                _hc_id_val = "" if _cand_hc == "(不关联)" else _cand_hc
                cm.add_candidate(_cand_name.strip(), _cand_role.strip(), _hc_id_val, _cand_source, _cand_linkedin, _cand_notes)
                st.success(f"✅ {_cand_name} 已加入 Pipeline（Sourced 阶段）。")
                st.rerun()
            else:
                st.warning("请至少填写候选人姓名和目标岗位。")

# --- Kanban 看板 (只显示活跃阶段) ---
st.markdown("### 🗂️ 招聘漏斗看板")
_active_only = st.checkbox("仅显示活跃候选人（隐藏 Hired / Rejected）", value=True)
_display_stages = _active_stages if _active_only else PIPELINE_STAGES

_kanban_cols = st.columns(len(_display_stages))
for _col_idx, _stage in enumerate(_display_stages):
    with _kanban_cols[_col_idx]:
        _color = STAGE_COLORS[_stage]
        st.markdown(
            f"<div style='background:{_color};color:#fff;text-align:center;"
            f"padding:6px;border-radius:6px 6px 0 0;font-weight:600;font-size:0.85rem;'>"
            f"{_stage} ({stats[_stage]})</div>",
            unsafe_allow_html=True,
        )
        _stage_candidates = cm.get_by_stage(_stage)
        if not _stage_candidates:
            st.markdown(
                "<div style='background:#F8FAFC;border:1px dashed #CBD5E1;border-top:none;"
                "border-radius:0 0 6px 6px;padding:16px;text-align:center;"
                "color:#94A3B8;font-size:0.8rem;'>Empty</div>",
                unsafe_allow_html=True,
            )
        for _cand in _stage_candidates:
            _score_badge = f"<span style='background:#EEF2FF;color:#4338CA;padding:1px 6px;border-radius:10px;font-size:0.72rem;'>Score: {html.escape(str(_cand['score']))}</span>" if _cand.get("score") is not None else ""
            st.markdown(
                f"<div style='background:#fff;border:1px solid #E2E8F0;border-radius:6px;"
                f"padding:10px 12px;margin-top:4px;'>"
                f"<div style='font-weight:600;font-size:0.9rem;'>{html.escape(_cand['name'])}</div>"
                f"<div style='color:#64748B;font-size:0.78rem;margin:2px 0;'>{html.escape(_cand['role'])}</div>"
                f"<div style='margin-top:4px;'>{_score_badge}</div>"
                f"<div style='color:#94A3B8;font-size:0.72rem;margin-top:4px;'>Updated {html.escape(_cand['updated_at'])}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            # Action buttons per card
            _next_stages = [s for s in PIPELINE_STAGES if s != _stage and s != "Rejected"]
            _move_to = st.selectbox("→", _next_stages, key=f"move_{_cand['id']}", label_visibility="collapsed")
            _move_note = st.text_input("备注", key=f"note_{_cand['id']}", placeholder="backward move requires note", label_visibility="collapsed")
            _act_cols = st.columns([1, 1])
            with _act_cols[0]:
                if st.button("移动", key=f"mv_{_cand['id']}", use_container_width=True):
                    try:
                        cm.move_stage(_cand["id"], _move_to, note=_move_note)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            with _act_cols[1]:
                if _stage != "Rejected":
                    if st.button("Reject", key=f"rej_{_cand['id']}", use_container_width=True, type="secondary"):
                        cm.move_stage(_cand["id"], "Rejected", note=_move_note or "Rejected from kanban")
                        st.rerun()

# --- 候选人详情 & 备注 ---
st.markdown("---")
st.markdown("### 📋 候选人详情 & 备注")
_all_cands = cm.get_all()
if not _all_cands:
    st.info("Pipeline 中暂无候选人。点击上方 '➕ 添加新候选人' 开始追踪。")
else:
    _cand_names = {f"{c['name']} ({c['stage']})": c["id"] for c in _all_cands}
    _selected_name = st.selectbox("选择候选人查看详情：", list(_cand_names.keys()))
    _selected_id = _cand_names[_selected_name]
    _selected = next((c for c in _all_cands if c["id"] == _selected_id), None)
    if _selected:
        _d1, _d2 = st.columns([1.5, 1])
        with _d1:
            st.markdown(f"**岗位：** {_selected['role']}")
            st.markdown(f"**来源：** {_selected['source'] or '—'}")
            if _selected.get("linkedin_url"):
                st.markdown(f"**LinkedIn：** [{_selected['linkedin_url']}]({_selected['linkedin_url']})")
            if _selected.get("hc_id"):
                st.markdown(f"**关联 HC：** `{_selected['hc_id']}`")
            st.markdown(f"**简历评分：** {_selected.get('score') or '未评分'}")
            st.markdown("**历史记录：**")
            for _h in reversed(_selected.get("history", [])):
                st.markdown(f"- `{_h['date']}` → **{_h['stage']}** — {_h.get('note','')}")
        with _d2:
            st.markdown("**当前备注：**")
            st.text_area("备注内容", value=_selected.get("notes", ""), height=120, key="notes_display", disabled=True)
            _new_note = st.text_input("追加备注", placeholder="输入新备注后点击保存...")
            _note_cols = st.columns(2)
            with _note_cols[0]:
                if st.button("💾 保存备注", use_container_width=True):
                    if _new_note.strip():
                        cm.add_note(_selected_id, _new_note.strip())
                        st.success("备注已保存")
                        st.rerun()
            with _note_cols[1]:
                if st.button("🗑️ 删除候选人", use_container_width=True, type="secondary"):
                    cm.delete_candidate(_selected_id)
                    st.warning(f"{_selected['name']} 已从 Pipeline 中移除。")
                    st.rerun()
