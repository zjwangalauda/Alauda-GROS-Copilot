"""Tests for document_parser.py — KeywordSearchEmbeddings & RAGSystem."""

import os
import sys
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Prevent Streamlit import side-effects.  document_parser.py does
# `import streamlit as st` at module level, and invalidate_rag_index() calls
# `st.cache_resource.clear()`.  We inject a lightweight mock before the first
# import so the real Streamlit is never loaded during testing.
# ---------------------------------------------------------------------------
_st_mock = MagicMock()
sys.modules.setdefault("streamlit", _st_mock)

from document_parser import KeywordSearchEmbeddings, RAGSystem, invalidate_rag_index  # noqa: E402


# ======================================================================
# KeywordSearchEmbeddings
# ======================================================================

class TestKeywordSearchEmbeddings:

    def test_embed_documents_returns_correct_shape(self):
        """embed_documents returns one 10-float vector per input text."""
        emb = KeywordSearchEmbeddings()
        texts = ["hello world", "foo bar baz"]
        result = emb.embed_documents(texts)

        assert isinstance(result, list)
        assert len(result) == len(texts)
        for vec in result:
            assert isinstance(vec, list)
            assert len(vec) == 10
            assert all(isinstance(v, float) for v in vec)

    def test_embed_documents_empty_list(self):
        """embed_documents with an empty list returns an empty list."""
        emb = KeywordSearchEmbeddings()
        assert emb.embed_documents([]) == []

    def test_embed_query_returns_correct_shape(self):
        """embed_query returns a single list of 10 floats."""
        emb = KeywordSearchEmbeddings()
        result = emb.embed_query("some query text")

        assert isinstance(result, list)
        assert len(result) == 10
        assert all(isinstance(v, float) for v in result)

    def test_call_works(self):
        """__call__ delegates to embed_query and returns the same shape."""
        emb = KeywordSearchEmbeddings()
        result = emb("another query")

        assert isinstance(result, list)
        assert len(result) == 10

    def test_call_matches_embed_query(self):
        """__call__ returns the same result as embed_query for the same input."""
        emb = KeywordSearchEmbeddings()
        text = "test text"
        assert emb(text) == emb.embed_query(text)


# ======================================================================
# RAGSystem — initialisation & properties
# ======================================================================

class TestRAGSystemInit:

    @patch.dict(os.environ, {}, clear=False)
    def test_keyword_mode_when_no_api_key(self):
        """RAGSystem falls back to keyword mode when EMBEDDING_API_KEY is absent."""
        env = os.environ.copy()
        env.pop("EMBEDDING_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            rag = RAGSystem(data_dir="/tmp/nonexistent_rag_test_dir")
            assert isinstance(rag.embeddings, KeywordSearchEmbeddings)
            assert rag.embedding_mode == "keyword"

    def test_embedding_mode_property_returns_keyword_by_default(self):
        """embedding_mode property returns 'keyword' when no real API key is set."""
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": ""}, clear=False):
            rag = RAGSystem(data_dir="/tmp/nonexistent_rag_test_dir")
            assert rag.embedding_mode == "keyword"

    def test_vector_store_starts_none(self):
        """vector_store is None right after construction."""
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": ""}, clear=False):
            rag = RAGSystem(data_dir="/tmp/nonexistent_rag_test_dir")
            assert rag.vector_store is None


# ======================================================================
# RAGSystem.retrieve
# ======================================================================

class TestRAGSystemRetrieve:

    def test_retrieve_returns_empty_when_vector_store_is_none(self):
        """retrieve() returns an empty string when vector_store has not been built."""
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": ""}, clear=False):
            rag = RAGSystem(data_dir="/tmp/nonexistent_rag_test_dir")
            assert rag.vector_store is None
            result = rag.retrieve("some query")
            assert result == ""


# ======================================================================
# RAGSystem.load_and_index
# ======================================================================

class TestRAGSystemLoadAndIndex:

    def test_load_and_index_returns_false_when_data_dir_missing(self, tmp_path):
        """load_and_index returns False when the data directory does not exist."""
        missing_dir = str(tmp_path / "does_not_exist")
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": ""}, clear=False):
            rag = RAGSystem(data_dir=missing_dir)
            assert rag.load_and_index() is False

    def test_load_and_index_returns_false_when_data_dir_empty(self, tmp_path):
        """load_and_index returns False when the data directory exists but has no files."""
        empty_dir = str(tmp_path / "empty_data")
        os.makedirs(empty_dir)
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": ""}, clear=False):
            rag = RAGSystem(data_dir=empty_dir)
            assert rag.load_and_index() is False

    def test_load_and_index_returns_true_when_vector_store_already_set(self, tmp_path):
        """load_and_index returns True immediately if vector_store is already populated."""
        with patch.dict(os.environ, {"EMBEDDING_API_KEY": ""}, clear=False):
            rag = RAGSystem(data_dir=str(tmp_path))
            rag.vector_store = MagicMock()  # pretend it is already built
            assert rag.load_and_index() is True


# ======================================================================
# invalidate_rag_index
# ======================================================================

class TestInvalidateRagIndex:

    def test_invalidate_does_not_crash_when_no_index_exists(self, tmp_path):
        """invalidate_rag_index runs without error even if the FAISS index dir is absent."""
        # Patch FAISS_INDEX_PATH to a guaranteed non-existent path
        with patch("document_parser.FAISS_INDEX_PATH", str(tmp_path / "nonexistent_faiss")):
            # Should not raise
            invalidate_rag_index()

    def test_invalidate_removes_existing_index_dir(self, tmp_path):
        """invalidate_rag_index removes the persisted FAISS index directory."""
        fake_index = tmp_path / "faiss_index"
        fake_index.mkdir()
        (fake_index / "index.faiss").write_text("dummy")

        with patch("document_parser.FAISS_INDEX_PATH", str(fake_index)):
            invalidate_rag_index()

        assert not fake_index.exists()
