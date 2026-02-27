import logging
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from candidate_manager import CandidateManager
from hc_manager import HCManager

logger = logging.getLogger(__name__)

st.markdown('<div class="main-title">📊 招聘效能数据看板</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">漏斗转化率 · 渠道 ROI · 岗位填补周期 · 简历评分分布</div>', unsafe_allow_html=True)

# --- 加载数据 ---
_hc_list = HCManager().get_all_requests()
_cand_list = CandidateManager().get_all()

# ── KPI 横幅 ──────────────────────────────────────────────
_active_hc = [h for h in _hc_list if h.get("status") == "Approved"]
_active_cands = [c for c in _cand_list if c.get("stage") not in ("Hired", "Rejected")]
_hired = [c for c in _cand_list if c.get("stage") == "Hired"]
_scored = [c for c in _cand_list if c.get("score") is not None]
_avg_score = round(sum(c["score"] for c in _scored) / len(_scored), 1) if _scored else None

_k1, _k2, _k3, _k4 = st.columns(4)
_k1.metric("🗂️ 开放 HC 数", len(_active_hc))
_k2.metric("👥 在途候选人", len(_active_cands))
_k3.metric("✅ 已入职", len(_hired))
_k4.metric("📊 平均简历评分", f"{_avg_score} / 100" if _avg_score else "—")

st.markdown("---")

# ── 第一行：漏斗 + 来源渠道 ────────────────────────────────
_col_funnel, _col_source = st.columns(2)

with _col_funnel:
    st.markdown("#### 🔻 招聘漏斗转化")
    _stage_order = ["Sourced", "Contacted", "Phone Screen", "Interview", "Offer", "Hired"]
    _stage_counts = {s: sum(1 for c in _cand_list if c.get("stage") == s) for s in _stage_order}
    if any(_stage_counts.values()):
        _funnel_df = pd.DataFrame({
            "阶段": list(_stage_counts.keys()),
            "候选人数": list(_stage_counts.values())
        }).set_index("阶段")
        st.bar_chart(_funnel_df, color="#004D99")
        # 转化率文字
        _prev = None
        for _s, _n in _stage_counts.items():
            if _prev is not None and _prev > 0:
                _rate = round(_n / _prev * 100)
                st.caption(f"{list(_stage_counts.keys())[list(_stage_counts.values()).index(_prev)]} → {_s}：{_rate}%")
            _prev = _n if _n > 0 else _prev
    else:
        st.info("暂无候选人数据。在模块七添加候选人后，漏斗图将自动生成。")

with _col_source:
    st.markdown("#### 📡 来源渠道分布")
    _source_counts: dict = {}
    for _c in _cand_list:
        _src = _c.get("source") or "Unknown"
        _source_counts[_src] = _source_counts.get(_src, 0) + 1
    if _source_counts:
        _src_df = pd.DataFrame({
            "渠道": list(_source_counts.keys()),
            "候选人数": list(_source_counts.values())
        }).set_index("渠道")
        st.bar_chart(_src_df, color="#10B981")
        # 渠道→入职率
        st.markdown("**渠道入职效率：**")
        for _src, _total in _source_counts.items():
            _src_hired = sum(1 for c in _cand_list if c.get("source") == _src and c.get("stage") == "Hired")
            _roi = round(_src_hired / _total * 100) if _total else 0
            st.caption(f"  {_src}：{_total} 人 → {_src_hired} 入职（{_roi}%）")
    else:
        st.info("暂无来源数据。")

# ── 第二行：评分分布 + HC 地区分布 ────────────────────────
_col_score, _col_region = st.columns(2)

with _col_score:
    st.markdown("#### 📈 简历评分分布")
    _scores = [c["score"] for c in _cand_list if c.get("score") is not None]
    if _scores:
        # 分段统计
        _buckets = {"<60 (淘汰)": 0, "60–79 (边缘)": 0, "80–89 (通过)": 0, "90+ (优秀)": 0}
        for _sc in _scores:
            if _sc < 60:   _buckets["<60 (淘汰)"] += 1
            elif _sc < 80: _buckets["60–79 (边缘)"] += 1
            elif _sc < 90: _buckets["80–89 (通过)"] += 1
            else:           _buckets["90+ (优秀)"] += 1
        _sc_df = pd.DataFrame({"档位": list(_buckets.keys()), "人数": list(_buckets.values())}).set_index("档位")
        st.bar_chart(_sc_df, color="#8B5CF6")
        st.caption(f"共 {len(_scores)} 份已评分简历，平均分 {_avg_score}")
    else:
        st.info("暂无评分数据。在模块三完成简历评分后，分布图将自动出现。")

with _col_region:
    st.markdown("#### 🌍 HC 需求地区分布")
    _region_counts: dict = {}
    for _h in _hc_list:
        _loc = _h.get("location") or "Unknown"
        _region_counts[_loc] = _region_counts.get(_loc, 0) + 1
    if _region_counts:
        _reg_df = pd.DataFrame({
            "地区": list(_region_counts.keys()),
            "HC 数量": list(_region_counts.values())
        }).set_index("地区")
        st.bar_chart(_reg_df, color="#F59E0B")
    else:
        st.info("暂无 HC 数据。")

# ── 第三行：岗位填补周期 ───────────────────────────────────
st.markdown("---")
st.markdown("#### ⏱️ 岗位填补周期（已入职候选人）")
_ttf_rows = []
for _c in _hired:
    try:
        _created = datetime.strptime(_c["created_at"], "%Y-%m-%d")
        _updated = datetime.strptime(_c["updated_at"], "%Y-%m-%d")
        _days = (_updated - _created).days
        _ttf_rows.append({"候选人": _c["name"], "岗位": _c["role"], "天数": _days})
    except Exception:
        logger.warning("Failed to compute time-to-fill for candidate %s", _c.get("id", "unknown"), exc_info=True)
if _ttf_rows:
    _ttf_df = pd.DataFrame(_ttf_rows)
    st.dataframe(_ttf_df, use_container_width=True)
    st.caption(f"平均填补周期：{round(sum(r['天数'] for r in _ttf_rows) / len(_ttf_rows))} 天")
else:
    st.info("当有候选人到达 Hired 阶段时，填补周期数据将显示在此处。")

# ── 第四行：HC 明细表 ─────────────────────────────────────
st.markdown("---")
st.markdown("#### 📋 HC 需求明细")
if _hc_list:
    _hc_df = pd.DataFrame([{
        "ID": h["id"], "日期": h["date"], "岗位": h["role_title"],
        "地区": h["location"], "部门": h["department"], "状态": h["status"]
    } for h in _hc_list])
    st.dataframe(_hc_df, use_container_width=True, hide_index=True)
else:
    st.info("暂无 HC 记录。")
