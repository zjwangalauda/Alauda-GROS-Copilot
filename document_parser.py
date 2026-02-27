import logging
import os
import shutil
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv(override=True)

FAISS_INDEX_PATH = "data/faiss_index"

class RAGSystem:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir

        emb_api_key = os.environ.get("EMBEDDING_API_KEY", "")

        if emb_api_key and "your_" not in emb_api_key:
            emb_api_base = os.environ.get("EMBEDDING_API_BASE", "https://api.openai.com/v1")
            try:
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=emb_api_key,
                    openai_api_base=emb_api_base
                )
                self._embedding_mode = "vector"
            except Exception:
                logger.warning("Failed to initialize OpenAI embeddings, falling back to keyword search", exc_info=True)
                self.embeddings = KeywordSearchEmbeddings()
                self._embedding_mode = "keyword"
        else:
            self.embeddings = KeywordSearchEmbeddings()
            self._embedding_mode = "keyword"

        self.vector_store = None
        self.all_chunks = []

    @property
    def embedding_mode(self):
        """Returns 'vector' (real semantic search) or 'keyword' (degraded fallback)."""
        return self._embedding_mode

    def load_and_index(self):
        if self.vector_store is not None:
            return True

        # --- Try loading persisted FAISS index first (skip rebuild if up-to-date) ---
        if self._embedding_mode == "vector" and os.path.exists(FAISS_INDEX_PATH):
            try:
                self.vector_store = FAISS.load_local(
                    FAISS_INDEX_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                return True
            except Exception:
                logger.warning("FAISS index corrupt or incompatible — rebuilding", exc_info=True)

        # --- Build index from source documents ---
        docs = []
        if not os.path.exists(self.data_dir):
            return False

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            if filename.endswith(".pdf"):
                try:
                    loader = PyPDFLoader(file_path)
                    docs.extend(loader.load())
                except Exception:
                    logger.warning("Failed to load PDF: %s", file_path, exc_info=True)
            elif filename.endswith(".md"):
                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs.extend(loader.load())
                except Exception:
                    logger.warning("Failed to load Markdown: %s", file_path, exc_info=True)

        if not docs:
            return False

        # Larger chunks preserve complete regulatory clauses (policy text is dense)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        splits = text_splitter.split_documents(docs)
        self.all_chunks = splits

        if not self.embeddings:
            return False

        try:
            self.vector_store = FAISS.from_documents(splits, self.embeddings)
            # Persist to disk so subsequent loads skip the rebuild
            if self._embedding_mode == "vector":
                self.vector_store.save_local(FAISS_INDEX_PATH)
            return True
        except Exception:
            logger.error("Failed to build FAISS vector store", exc_info=True)
            return False

    def retrieve(self, query, k=5):
        if not self.vector_store:
            return ""

        # Keyword fallback: intercept before FAISS (pseudo-vectors are useless for similarity)
        if isinstance(self.embeddings, KeywordSearchEmbeddings):
            matched_docs = []
            keywords = [
                word for word in query.replace("?", "").replace("?", "").split()
                if len(word) > 1
            ]
            for doc in self.all_chunks:
                text = doc.page_content.lower()
                if any(kw.lower() in text for kw in keywords):
                    matched_docs.append(doc.page_content)
            if matched_docs:
                return "\n\n".join(list(dict.fromkeys(matched_docs))[:k])
            return ""

        # Real vector similarity search
        results = self.vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in results])


def invalidate_rag_index():
    """
    Call this after updating the knowledge base (Module 6 compile).
    Deletes the persisted FAISS index so Module 5 rebuilds with fresh content,
    and clears Streamlit's resource cache so the RAGSystem object is re-created.
    """
    if os.path.exists(FAISS_INDEX_PATH):
        shutil.rmtree(FAISS_INDEX_PATH)
    st.cache_resource.clear()


class KeywordSearchEmbeddings:
    """Placeholder that lets FAISS initialise without an embedding API.
    Actual retrieval is intercepted in RAGSystem.retrieve() and handled
    via keyword matching instead."""
    def embed_documents(self, texts):
        return [[0.0] * 10 for _ in texts]

    def embed_query(self, text):
        return [0.0] * 10

    def __call__(self, text):
        return self.embed_query(text)
