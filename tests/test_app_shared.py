"""Tests for app_shared.py — security imports, cache key helpers."""

import os
import sys
from unittest.mock import patch, MagicMock



# ---------------------------------------------------------------------------
# Ensure streamlit is mocked so app_shared can be imported without a running
# Streamlit server.  We also mock db.get_db which is called at module level.
# ---------------------------------------------------------------------------
_st_mock = MagicMock()
sys.modules.setdefault("streamlit", _st_mock)


# ======================================================================
# Verify security fix: hmac is imported
# ======================================================================

class TestHmacImport:

    def test_hmac_is_imported_in_module(self):
        """app_shared.py must import hmac (used for constant-time password comparison)."""
        import app_shared
        # The module should have 'hmac' in its namespace (via `import hmac`)
        assert hasattr(app_shared, "hmac")
        # Double-check it is the real hmac module
        import hmac as real_hmac
        assert app_shared.hmac is real_hmac

    def test_hmac_compare_digest_available(self):
        """hmac.compare_digest must be callable (used in check_password)."""
        import app_shared
        assert callable(app_shared.hmac.compare_digest)


# ======================================================================
# Cache key helpers
# ======================================================================

class TestLlmCacheKey:

    def test_returns_tuple(self):
        """_llm_cache_key must return a tuple."""
        from app_shared import _llm_cache_key
        result = _llm_cache_key()
        assert isinstance(result, tuple)

    def test_tuple_has_four_elements(self):
        """_llm_cache_key returns a 4-tuple (API_KEY, API_BASE, MODEL, STRONG_MODEL)."""
        from app_shared import _llm_cache_key
        result = _llm_cache_key()
        assert len(result) == 4

    def test_reflects_env_variables(self):
        """_llm_cache_key captures the current environment values."""
        from app_shared import _llm_cache_key
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-key-123",
            "OPENAI_API_BASE": "https://custom.api/v1",
            "LLM_MODEL": "gpt-4o",
            "STRONG_MODEL": "gpt-4o-strong",
        }, clear=False):
            result = _llm_cache_key()
            assert result == ("sk-test-key-123", "https://custom.api/v1", "gpt-4o", "gpt-4o-strong")

    def test_different_env_produces_different_key(self):
        """Changing an env var must change the cache key (invalidation guarantee)."""
        from app_shared import _llm_cache_key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key-A"}, clear=False):
            key_a = _llm_cache_key()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key-B"}, clear=False):
            key_b = _llm_cache_key()
        assert key_a != key_b


class TestEmbCacheKey:

    def test_returns_tuple(self):
        """_emb_cache_key must return a tuple."""
        from app_shared import _emb_cache_key
        result = _emb_cache_key()
        assert isinstance(result, tuple)

    def test_tuple_has_two_elements(self):
        """_emb_cache_key returns a 2-tuple (EMBEDDING_API_KEY, EMBEDDING_API_BASE)."""
        from app_shared import _emb_cache_key
        result = _emb_cache_key()
        assert len(result) == 2

    def test_reflects_env_variables(self):
        """_emb_cache_key captures the current embedding env values."""
        from app_shared import _emb_cache_key
        with patch.dict(os.environ, {
            "EMBEDDING_API_KEY": "emb-key-456",
            "EMBEDDING_API_BASE": "https://emb.api/v1",
        }, clear=False):
            result = _emb_cache_key()
            assert result == ("emb-key-456", "https://emb.api/v1")

    def test_different_env_produces_different_key(self):
        """Changing an embedding env var must change the cache key."""
        from app_shared import _emb_cache_key
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": "emb-A"}, clear=False):
            key_a = _emb_cache_key()
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": "emb-B"}, clear=False):
            key_b = _emb_cache_key()
        assert key_a != key_b
