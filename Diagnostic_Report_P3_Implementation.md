# Diagnostic Report: P3 Implementation (Complete)

**Commits:** `ad382d7` + `82fe85d`
**Date:** 2026-02-28
**Branch:** `main`
**Combined scope:** 6 files changed, +145 / −15 lines (excluding diagnostic report)

---

## 1. Executive Summary

This report covers the full P3 implementation — all 6 recommendations (R1–R6) identified in the P2 diagnostic report. The changes span three categories: **error handling hardening** (R1, R2), **test coverage gaps** (R3, R4), and **UX/observability improvements** (R5, R6). All 39 tests pass with zero regressions.

| R# | Description | Status | Commit |
|----|-------------|--------|--------|
| R1 | `try/except` in `extract_web_knowledge()` | Done | `ad382d7` |
| R2 | Defensive `fut.result()` guard in mod3 | Done | `ad382d7` |
| R3 | Integration tests for `extract_web_knowledge()` | Done | `ad382d7` |
| R4 | Tests for move-out-of-Rejected validation | Done | `ad382d7` |
| R5 | "Reject" button on kanban cards | Done | `82fe85d` |
| R6 | Structured retry logging in `_call_llm()` | Done | `82fe85d` |

---

## 2. Change-by-Change Analysis

### 2.1 R1: Error Handling in `extract_web_knowledge()` (`recruitment_agent.py:388–396`)

**Before:** The LLM call was unguarded — if `_call_llm()` raised after retry exhaustion, the exception propagated raw to the Streamlit UI via `mod6_knowledge_harvester.py`.

**After:** Wrapped in `try/except Exception`, returning `f"❌ Knowledge extraction failed: {str(e)}"` on failure. This matches the pattern used by all other agent methods (`generate_jd_and_xray`, `evaluate_resume`, etc.).

**Assessment:** Correct. The caller in `mod6_knowledge_harvester.py:71` checks for `"EXTRACTION_FAILED" in ai_result`, which won't match the `"❌"` prefix, so the error string flows through to the outer `except` block at line 81 and displays properly via `st.error()`.

**Residual risk:** None.

---

### 2.2 R2: Defensive Guard on `fut.result()` (`pages/mod3_resume_matcher.py:78–85`)

**Before:** `fut.result()` was called without `try/except`. If a worker thread raised an unexpected exception (beyond what `evaluate_resume()`'s own handler catches), the entire Streamlit page would crash.

**After:**
```python
try:
    idx, result = fut.result()
    results[idx] = result
except Exception as e:
    idx = futures[fut]
    results[idx] = f"❌ Evaluation failed: {str(e)}"
    error_indices.add(idx)
```

The `futures[fut]` lookup (line 83) recovers the original index from the future→index mapping, so the error can be displayed in the correct position during Phase 3.

**Assessment:** Correct. The `error_indices` set ensures failed evaluations display as `st.error()` rather than attempting to render markdown. The progress bar still increments correctly because `completed_count += 1` is outside the `try/except` block (line 86).

**Residual risk:** None.

---

### 2.3 R3: Integration Tests for `extract_web_knowledge()` (`tests/test_extract_web_knowledge.py`)

**4 new tests** (92 lines):

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_extract_web_knowledge_success` | Mocked LLM returns policy text | Result contains expected content; `create()` called once |
| `test_extract_web_knowledge_extraction_failed` | Mocked LLM returns "EXTRACTION_FAILED" | Result contains "EXTRACTION_FAILED" |
| `test_extract_web_knowledge_error_handled` | Mocked LLM raises `RateLimitError` persistently | Result starts with "❌", contains "failed" |
| `test_extract_web_knowledge_no_client` | `agent.client = None` | Returns `None` |

**Assessment:** Good coverage of the four distinct code paths through the method: success, extraction failure (LLM says no relevant info), LLM error (after retries), and missing client. The `_make_rate_limit_error()` helper properly constructs a realistic `RateLimitError` with mock response object.

**Residual risk:** None.

---

### 2.4 R4: Tests for Move-out-of-Rejected (`tests/test_candidate_manager.py:112–127`)

**2 new tests:**

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_move_out_of_rejected_requires_note` | Rejected → Phone Screen without note | Raises `ValueError` matching "note is required" |
| `test_move_out_of_rejected_with_note_succeeds` | Rejected → Phone Screen with note | Returns `True`, stage updated correctly |

**Assessment:** These complement the existing `test_move_to_rejected_always_allowed` and `test_backward_move_requires_note` tests, completing the state transition matrix for the Rejected stage. The `is_leaving_rejected` branch in `candidate_manager.py:85` is now fully covered.

**Residual risk:** None.

---

### 2.5 R5: "Reject" Button on Kanban Cards (`pages/mod7_candidate_pipeline.py:90–106`)

**Before:** Users could only reject candidates via the stage dropdown (which explicitly excluded "Rejected" from options). The only way to reject was through the detail panel.

**After:** Each kanban card now shows two side-by-side buttons:
- **"移动"** (left) — moves to the selected stage, with `try/except ValueError` for backward-move validation
- **"Reject"** (right, `type="secondary"`) — one-click rejection, auto-fills note as `"Rejected from kanban"` if the note field is empty

The Reject button is conditionally hidden when `_stage == "Rejected"` (line 103), avoiding a no-op button on already-rejected cards.

**Assessment:** Good UX improvement. The `_move_note or "Rejected from kanban"` default (line 105) ensures the history log always has a meaningful note. The `type="secondary"` styling visually distinguishes rejection from normal moves.

**Residual risks:**
- **Cosmetic:** The two-column button layout slightly increases card height. With many candidates in a single stage column, vertical scrolling increases. This is acceptable for the added functionality.
- **Note:** When the kanban is in "active only" mode (default), Rejected candidates are hidden, so the user gets immediate visual feedback — the card disappears after rejection.

---

### 2.6 R6: Structured Retry Logging (`recruitment_agent.py:58–70`)

**What changed:**
- Added `before_sleep=before_sleep_log(logger, logging.WARNING)` — tenacity logs a WARNING before each retry sleep, including wait duration and exception details
- Added `after=after_log(logger, logging.DEBUG)` — tenacity logs a DEBUG message after each call attempt with outcome
- Added manual `logger.warning("LLM call attempt %d/3 (model=%s)", attempt, model)` inside the method body for attempt 2+ (lines 68–70)

**Log output examples:**
```
WARNING  recruitment_agent: Retrying _call_llm in 1.0 seconds as it raised RateLimitError: rate limit.
WARNING  recruitment_agent: LLM call attempt 2/3 (model=claude-haiku-4-5-20251001)
DEBUG    recruitment_agent: Finished call to '_call_llm' after 2.1s, this was the 2nd time calling it.
```

**Assessment:** The three-layer logging provides good observability:
1. `before_sleep_log` — alerts ops that a retry is about to happen and why
2. Manual `attempt` log — provides the business context (model name, attempt count)
3. `after_log` — provides timing data for each attempt

The `self._call_llm.retry.statistics.get("attempt_number", 1)` access (line 68) reads tenacity's internal statistics dict. The default value `1` ensures no `KeyError` on the first call before statistics are populated.

**Residual risks:**
- **Minor:** `retry.statistics` is a tenacity implementation detail, not a documented public API. However, it has been stable across tenacity versions 8.x and is unlikely to change. If it does, the `get(..., 1)` default gracefully degrades — the manual log simply never fires.
- **Log volume:** In a burst of rate-limited calls across multiple agent methods, the WARNING logs could be noisy. This is acceptable — rate limiting is an operational event that warrants visibility.

---

## 3. Test Suite Summary

```
tests/test_candidate_manager.py    14 tests (12 prev + 2 new)   PASSED
tests/test_extract_web_knowledge.py 4 tests (all new)           PASSED
tests/test_hc_manager.py            9 tests (unchanged)         PASSED
tests/test_knowledge_manager.py     7 tests (unchanged)         PASSED
tests/test_pydantic_validation.py   3 tests (unchanged)         PASSED
tests/test_retry.py                 2 tests (unchanged)         PASSED
─────────────────────────────────────────────────────────────────
TOTAL                               39 tests                    ALL PASSED
Runtime                             9.32s
```

**Coverage delta:** +6 tests from P3 (4 for `extract_web_knowledge`, 2 for Rejected transitions). Total test count has grown from 25 (pre-P2) → 33 (post-P2) → 39 (post-P3).

---

## 4. Cumulative Status

All P2 and P3 recommendations are now fully implemented:

| Phase | Items | Tests Added | Status |
|-------|-------|-------------|--------|
| P2 (5 tasks) | Retry, state machine, parallelization, Pydantic, deps | +8 | Complete |
| P3 (6 items R1–R6) | Error handling, guards, tests, Reject button, logging | +6 | Complete |
| **Total** | **11 items** | **14 new tests (39 total)** | **All done** |

---

## 5. Forward-Looking Observations

No blocking issues remain. The following are optional enhancements for future consideration:

| # | Observation | Severity | Description |
|---|-------------|----------|-------------|
| O1 | Info | The kanban "Reject" button bypasses the stage dropdown validation — it calls `move_stage()` directly with `"Rejected"`. This is intentional and correct (rejection is always allowed), but the UX could be enhanced with a confirmation dialog for accidental clicks. |
| O2 | Info | `extract_web_knowledge()` returns `None` when `self.client` is missing (line 371). While the UI gates on API key presence, a more defensive approach would be to return `"EXTRACTION_FAILED"` instead, eliminating the `None` code path entirely. |
| O3 | Info | The test suite has no coverage for the Streamlit UI layer (pages/). Consider adding `pytest-streamlit` or manual smoke tests as a future quality gate. |
