import os
from unittest.mock import MagicMock, patch

import pytest
from openai import RateLimitError

from recruitment_agent import RecruitmentAgent


def _make_rate_limit_error():
    """Create a realistic RateLimitError for testing."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}
    mock_response.json.return_value = {"error": {"message": "rate limit", "type": "rate_limit"}}
    return RateLimitError("rate limit", response=mock_response, body=None)


def _make_success_response(content="OK"):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_retry_on_rate_limit_then_succeed():
    """_call_llm retries on RateLimitError and eventually succeeds."""
    agent = RecruitmentAgent()
    agent.client = MagicMock()

    # Fail twice with RateLimitError, then succeed
    agent.client.chat.completions.create.side_effect = [
        _make_rate_limit_error(),
        _make_rate_limit_error(),
        _make_success_response("Success after retries"),
    ]

    result = agent._call_llm(
        model="test-model",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.1,
    )
    assert result.choices[0].message.content == "Success after retries"
    assert agent.client.chat.completions.create.call_count == 3


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_retry_exhausted_raises():
    """After max retries, the original exception is re-raised."""
    agent = RecruitmentAgent()
    agent.client = MagicMock()

    agent.client.chat.completions.create.side_effect = _make_rate_limit_error()

    with pytest.raises(RateLimitError):
        agent._call_llm(
            model="test-model",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.1,
        )
    assert agent.client.chat.completions.create.call_count == 3
