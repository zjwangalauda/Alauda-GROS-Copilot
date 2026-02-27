import sys
import os

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recruitment_agent import TranslatedHCFields


def test_valid_json_parses():
    raw = '{"role_title":"Backend Developer","location":"Singapore","mission":"Build platform","tech_stack":"Python, K8s","deal_breakers":"None","selling_point":"Global team"}'
    result = TranslatedHCFields.model_validate_json(raw)
    assert result.role_title == "Backend Developer"
    assert result.location == "Singapore"
    assert result.tech_stack == "Python, K8s"


def test_missing_field_raises():
    raw = '{"role_title":"Dev","location":"SG"}'
    with pytest.raises(ValidationError):
        TranslatedHCFields.model_validate_json(raw)


def test_invalid_json_raises():
    with pytest.raises(ValidationError):
        TranslatedHCFields.model_validate_json("not json at all")
