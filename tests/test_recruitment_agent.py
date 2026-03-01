"""Tests for recruitment_agent.py — no-client behaviour, file parsing, constants."""

import os
from unittest.mock import patch


from recruitment_agent import RecruitmentAgent, MAX_INPUT_CHARS, get_llm_usage_log


# ======================================================================
# Agent initialises without an API key
# ======================================================================

class TestRecruitmentAgentNoKey:

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    def test_init_with_no_api_key_sets_client_none(self):
        """When OPENAI_API_KEY is empty, client should be None."""
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            agent = RecruitmentAgent()
            assert agent.client is None

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    def test_init_with_empty_api_key_sets_client_none(self):
        """When OPENAI_API_KEY is explicitly empty string, client should be None."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            agent = RecruitmentAgent()
            assert agent.client is None


# ======================================================================
# Methods return warnings when no client
# ======================================================================

class TestNoClientWarnings:
    """All LLM-dependent methods should return a warning string when client is None."""

    def _make_agent_no_client(self):
        agent = RecruitmentAgent.__new__(RecruitmentAgent)
        agent.client = None
        agent.api_key = None
        agent.base_url = ""
        agent.model = "test"
        agent.strong_model = "test"
        agent.system_prompt = ""
        return agent

    def test_generate_jd_and_xray_returns_warning(self):
        agent = self._make_agent_no_client()
        result = agent.generate_jd_and_xray(
            role_title="Dev",
            location="SG",
            mission="Build",
            tech_stack="Python",
            deal_breakers="None",
            selling_point="Great",
        )
        assert "OPENAI_API_KEY" in result
        assert result.startswith("\u26a0")  # warning sign

    def test_generate_interview_scorecard_returns_warning(self):
        agent = self._make_agent_no_client()
        result = agent.generate_interview_scorecard(jd_text="Some JD text")
        assert "OPENAI_API_KEY" in result
        assert result.startswith("\u26a0")

    def test_generate_outreach_message_returns_warning(self):
        agent = self._make_agent_no_client()
        result = agent.generate_outreach_message(jd_text="JD", candidate_info="Info")
        assert "OPENAI_API_KEY" in result
        assert result.startswith("\u26a0")

    def test_evaluate_resume_returns_warning(self):
        agent = self._make_agent_no_client()
        result = agent.evaluate_resume(jd_text="JD", resume_text="Resume")
        assert "OPENAI_API_KEY" in result
        assert result.startswith("\u26a0")

    def test_answer_playbook_question_returns_warning(self):
        agent = self._make_agent_no_client()
        result = agent.answer_playbook_question(query="What?", context_docs="ctx")
        assert "OPENAI_API_KEY" in result
        assert result.startswith("\u26a0")

    def test_translate_hc_fields_returns_original_fields(self):
        agent = self._make_agent_no_client()
        fields = {
            "role_title": "后端开发",
            "location": "北京",
            "mission": "搭建微服务",
            "tech_stack": "Python",
            "deal_breakers": "无",
            "selling_point": "好团队",
        }
        result = agent.translate_hc_fields(fields)
        assert result == fields  # returned unchanged


# ======================================================================
# extract_text_from_file
# ======================================================================

class TestExtractTextFromFile:

    def _make_agent(self):
        agent = RecruitmentAgent.__new__(RecruitmentAgent)
        agent.client = None
        agent.api_key = None
        return agent

    def test_txt_bytes_decoded_correctly(self):
        """A .txt file's bytes are decoded as UTF-8 text."""
        agent = self._make_agent()
        content = "Hello, this is a plain text resume."
        result = agent.extract_text_from_file("resume.txt", content.encode("utf-8"))
        assert result == content

    def test_txt_unicode_decoded_correctly(self):
        """A .txt file with unicode characters is decoded properly."""
        agent = self._make_agent()
        content = "Resume for 张三 — Senior Engineer"
        result = agent.extract_text_from_file("cv.TXT", content.encode("utf-8"))
        assert result == content

    def test_unsupported_format_returns_error_message(self):
        """An unsupported file extension returns a descriptive error string."""
        agent = self._make_agent()
        result = agent.extract_text_from_file("resume.jpg", b"\xff\xd8\xff")
        assert "Unsupported file format" in result
        assert "PDF" in result

    def test_unsupported_format_xlsx(self):
        """An .xlsx file is not supported."""
        agent = self._make_agent()
        result = agent.extract_text_from_file("data.xlsx", b"\x00\x00")
        assert "Unsupported file format" in result


# ======================================================================
# Module-level constants and helpers
# ======================================================================

class TestModuleConstants:

    def test_max_input_chars_is_positive_integer(self):
        """MAX_INPUT_CHARS must be a positive integer."""
        assert isinstance(MAX_INPUT_CHARS, int)
        assert MAX_INPUT_CHARS > 0

    def test_get_llm_usage_log_returns_list(self):
        """get_llm_usage_log always returns a list."""
        result = get_llm_usage_log()
        assert isinstance(result, list)

    def test_get_llm_usage_log_capped_at_50(self):
        """get_llm_usage_log returns at most 50 entries."""
        result = get_llm_usage_log()
        assert len(result) <= 50
