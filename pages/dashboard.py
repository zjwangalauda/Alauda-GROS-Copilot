import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from candidate_manager import CandidateManager
from hc_manager import HCManager
from recruitment_agent import get_llm_usage_log
from app_shared import bi

logger = logging.getLogger(__name__)

st.markdown('<div class="main-title">📊 Recruitment Performance Dashboard / 招聘效能数据看板</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Funnel Conversion · Channel ROI · Time-to-Fill · Resume Score Distribution\n漏斗转化率 · 渠道 ROI · 岗位填补周期 · 简历评分分布</div>', unsafe_allow_html=True)

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
_k1.metric(bi("🗂️ Open HCs", "🗂️ 开放 HC 数"), len(_active_hc))
_k2.metric(bi("👥 Active Candidates", "👥 在途候选人"), len(_active_cands))
_k3.metric(bi("✅ Hired", "✅ 已入职"), len(_hired))
_k4.metric(bi("📊 Avg Resume Score", "📊 平均简历评分"), f"{_avg_score} / 100" if _avg_score else "—")

st.markdown("---")

# ── 第一行：漏斗 + 来源渠道 ────────────────────────────────
_col_funnel, _col_source = st.columns(2)

with _col_funnel:
    st.markdown("#### 🔻 Recruitment Funnel / 招聘漏斗转化")
    _stage_order = ["Sourced", "Contacted", "Phone Screen", "Interview", "Offer", "Hired"]
    _stage_counts = {s: sum(1 for c in _cand_list if c.get("stage") == s) for s in _stage_order}
    if any(_stage_counts.values()):
        _funnel_df = pd.DataFrame({
            "Stage / 阶段": list(_stage_counts.keys()),
            "Candidates / 候选人数": list(_stage_counts.values())
        }).set_index("Stage / 阶段")
        st.bar_chart(_funnel_df, color="#004D99")
        # 转化率文字
        _prev = None
        for _s, _n in _stage_counts.items():
            if _prev is not None and _prev > 0:
                _rate = round(_n / _prev * 100)
                st.caption(f"{list(_stage_counts.keys())[list(_stage_counts.values()).index(_prev)]} → {_s}：{_rate}%")
            _prev = _n if _n > 0 else _prev
    else:
        st.info(bi("No candidate data. Add candidates in Module 7 for funnel chart.", "暂无候选人数据。在模块七添加候选人后，漏斗图将自动生成。"))

with _col_source:
    st.markdown("#### 📡 Source Channel Distribution / 来源渠道分布")
    _source_counts: dict = {}
    for _c in _cand_list:
        _src = _c.get("source") or "Unknown"
        _source_counts[_src] = _source_counts.get(_src, 0) + 1
    if _source_counts:
        _src_df = pd.DataFrame({
            "Channel / 渠道": list(_source_counts.keys()),
            "Candidates / 候选人数": list(_source_counts.values())
        }).set_index("Channel / 渠道")
        st.bar_chart(_src_df, color="#10B981")
        # 渠道→入职率
        st.markdown("**Channel Hire Rate / 渠道入职效率：**")
        for _src, _total in _source_counts.items():
            _src_hired = sum(1 for c in _cand_list if c.get("source") == _src and c.get("stage") == "Hired")
            _roi = round(_src_hired / _total * 100) if _total else 0
            st.caption(f"  {_src}: {_total} → {_src_hired} hired ({_roi}%) / {_total} 人 → {_src_hired} 入职（{_roi}%）")
    else:
        st.info(bi("No source data yet.", "暂无来源数据。"))

# ── 第二行：评分分布 + HC 地区分布 ────────────────────────
_col_score, _col_region = st.columns(2)

with _col_score:
    st.markdown("#### 📈 Resume Score Distribution / 简历评分分布")
    _scores = [c["score"] for c in _cand_list if c.get("score") is not None]
    if _scores:
        # 分段统计
        _buckets = {"<60 Reject / 淘汰": 0, "60–79 Borderline / 边缘": 0, "80–89 Pass / 通过": 0, "90+ Excellent / 优秀": 0}
        for _sc in _scores:
            if _sc < 60:
                _buckets["<60 Reject / 淘汰"] += 1
            elif _sc < 80:
                _buckets["60–79 Borderline / 边缘"] += 1
            elif _sc < 90:
                _buckets["80–89 Pass / 通过"] += 1
            else:
                _buckets["90+ Excellent / 优秀"] += 1
        _sc_df = pd.DataFrame({"Tier / 档位": list(_buckets.keys()), "Count / 人数": list(_buckets.values())}).set_index("Tier / 档位")
        st.bar_chart(_sc_df, color="#8B5CF6")
        st.caption(bi(f"{len(_scores)} scored resumes, avg {_avg_score}", f"共 {len(_scores)} 份已评分简历，平均分 {_avg_score}"))
    else:
        st.info(bi("No score data. Complete resume scoring in Module 3 for distribution chart.", "暂无评分数据。在模块三完成简历评分后，分布图将自动出现。"))

with _col_region:
    st.markdown("#### 🌍 HC Region Distribution / HC 需求地区分布")
    _region_counts: dict = {}
    for _h in _hc_list:
        _loc = _h.get("location") or "Unknown"
        _region_counts[_loc] = _region_counts.get(_loc, 0) + 1
    if _region_counts:
        _reg_df = pd.DataFrame({
            "Region / 地区": list(_region_counts.keys()),
            "HC Count / HC 数量": list(_region_counts.values())
        }).set_index("Region / 地区")
        st.bar_chart(_reg_df, color="#F59E0B")
    else:
        st.info(bi("No HC data yet.", "暂无 HC 数据。"))

# ── 第三行：岗位填补周期 ───────────────────────────────────
st.markdown("---")
st.markdown("#### ⏱️ Time-to-Fill (Hired Candidates) / 岗位填补周期")
_ttf_rows = []
for _c in _hired:
    try:
        _created = datetime.strptime(_c["created_at"], "%Y-%m-%d")
        _updated = datetime.strptime(_c["updated_at"], "%Y-%m-%d")
        _days = (_updated - _created).days
        _ttf_rows.append({"Candidate / 候选人": _c["name"], "Role / 岗位": _c["role"], "Days / 天数": _days})
    except Exception:
        logger.warning("Failed to compute time-to-fill for candidate %s", _c.get("id", "unknown"), exc_info=True)
if _ttf_rows:
    _ttf_df = pd.DataFrame(_ttf_rows)
    st.dataframe(_ttf_df, use_container_width=True)
    st.caption(bi(f"Avg time-to-fill: {round(sum(r['Days / 天数'] for r in _ttf_rows) / len(_ttf_rows))} days", f"平均填补周期：{round(sum(r['Days / 天数'] for r in _ttf_rows) / len(_ttf_rows))} 天"))
else:
    st.info(bi("Time-to-fill data appears when candidates reach Hired stage.", "当有候选人到达 Hired 阶段时，填补周期数据将显示在此处。"))

# ── 第四行：HC 明细表 ─────────────────────────────────────
st.markdown("---")
st.markdown("#### 📋 HC Request Details / HC 需求明细")
if _hc_list:
    _hc_df = pd.DataFrame([{
        "ID": h["id"], "Date / 日期": h["date"], "Role / 岗位": h["role_title"],
        "Region / 地区": h["location"], "Dept / 部门": h["department"], "Status / 状态": h["status"]
    } for h in _hc_list])
    st.dataframe(_hc_df, use_container_width=True, hide_index=True)
else:
    st.info(bi("No HC records.", "暂无 HC 记录。"))

# ── 第五行：LLM Token 使用追踪 ─────────────────────────────
st.markdown("---")
st.markdown("#### 🤖 Recent LLM Usage / 近期 LLM 调用记录")
_usage_log = get_llm_usage_log()
if _usage_log:
    _usage_df = pd.DataFrame(_usage_log)
    _usage_df = _usage_df[["timestamp", "model", "prompt_tokens", "completion_tokens", "total_tokens"]]
    _usage_df.columns = ["Time / 时间", "Model / 模型", "Prompt Tokens", "Completion Tokens", "Total Tokens / 总 Tokens"]
    st.dataframe(_usage_df.iloc[::-1], use_container_width=True, hide_index=True)
    _total = sum(r["total_tokens"] for r in _usage_log)
    st.caption(bi(f"Session total: {_total:,} tokens ({len(_usage_log)} calls)", f"本次会话累计消耗 {_total:,} tokens（最近 {len(_usage_log)} 次调用）"))
else:
    st.info(bi("No LLM calls this session. Token usage appears after using other modules.", "本次会话尚未发起 LLM 调用。使用其他模块后，此处将显示 Token 消耗记录。"))
