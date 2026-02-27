import sys
import os
from unittest.mock import MagicMock, patch

import pytest
from openai import RateLimitError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recruitment_agent import RecruitmentAgent


def _make_success_response(content):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_rate_limit_error():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}
    mock_response.json.return_value = {"error": {"message": "rate limit", "type": "rate_limit"}}
    return RateLimitError("rate limit", response=mock_response, body=None)


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_extract_web_knowledge_success():
    """extract_web_knowledge returns LLM content on success."""
    agent = RecruitmentAgent()
    agent.client = MagicMock()
    agent.client.chat.completions.create.return_value = _make_success_response(
        "Singapore EP minimum salary: SGD 5,600 from Sep 2025."
    )

    result = agent.extract_web_knowledge(
        target_url="https://example.com/policy",
        region="Singapore",
        category="Visa/EP",
        raw_text="Some raw scraped text about EP policy...",
    )
    assert "SGD 5,600" in result
    agent.client.chat.completions.create.assert_called_once()


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_extract_web_knowledge_extraction_failed():
    """extract_web_knowledge returns EXTRACTION_FAILED when LLM finds nothing relevant."""
    agent = RecruitmentAgent()
    agent.client = MagicMock()
    agent.client.chat.completions.create.return_value = _make_success_response("EXTRACTION_FAILED")

    result = agent.extract_web_knowledge(
        target_url="https://example.com/irrelevant",
        region="Singapore",
        category="Visa/EP",
        raw_text="Totally unrelated content about cooking recipes.",
    )
    assert "EXTRACTION_FAILED" in result


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_extract_web_knowledge_error_handled():
    """extract_web_knowledge returns error string on LLM failure (after retries exhausted)."""
    agent = RecruitmentAgent()
    agent.client = MagicMock()
    agent.client.chat.completions.create.side_effect = _make_rate_limit_error()

    result = agent.extract_web_knowledge(
        target_url="https://example.com/policy",
        region="Singapore",
        category="Visa/EP",
        raw_text="Some text",
    )
    assert result.startswith("❌")
    assert "failed" in result.lower()


def test_extract_web_knowledge_no_client():
    """extract_web_knowledge returns None when client is not configured."""
    agent = RecruitmentAgent()
    agent.client = None

    result = agent.extract_web_knowledge(
        target_url="https://example.com",
        region="Singapore",
        category="Visa/EP",
        raw_text="text",
    )
    assert result is None
