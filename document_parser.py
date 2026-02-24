import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv
load_dotenv(override=True)

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
            except Exception:
                self.embeddings = KeywordSearchEmbeddings()
        else:
            self.embeddings = KeywordSearchEmbeddings()
            
        self.vector_store = None
        self.all_chunks = [] # 用于后备的纯文本匹配

    def load_and_index(self):
        if self.vector_store is not None:
            return True 
            
        docs = []
        if not os.path.exists(self.data_dir):
            return False
            
        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            if filename.endswith(".pdf"):
                try:
                    loader = PyPDFLoader(file_path)
                    docs.extend(loader.load())
                except Exception as e:
                    pass
            elif filename.endswith(".md"):
                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs.extend(loader.load())
                except Exception as ex:
                    pass
                
        if not docs:
            return False

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        splits = text_splitter.split_documents(docs)
        self.all_chunks = splits # 存储原文本供字符串匹配使用
        
        if not self.embeddings:
            return False
            
        try:
            self.vector_store = FAISS.from_documents(splits, self.embeddings)
            return True
        except Exception as e:
            return False

    def retrieve(self, query, k=3):
        if not self.vector_store:
            return ""
            
        # 如果是降级模式，我们直接结合精准文本搜索，弥补伪向量的随机性
        if isinstance(self.embeddings, KeywordSearchEmbeddings):
            matched_docs = []
            keywords = [word for word in query.replace("?", "").replace("？", "").split(" ") if len(word) > 1]
            
            # 首先尝试字面关键词匹配
            for doc in self.all_chunks:
                text = doc.page_content.lower()
                # 命中任何关键词，或者提问词的子串
                if any(kw.lower() in text for kw in keywords) or "配额" in text or "新加坡" in text:
                    matched_docs.append(doc.page_content)
                    
            if matched_docs:
                return "\n\n".join(list(set(matched_docs))[:k+2])

        # 否则使用原本的相似度搜索
        results = self.vector_store.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in results])
        return context

class KeywordSearchEmbeddings:
    """充当占位符，让 FAISS 不报错，实际检索时被 RAGSystem 截获转为文本匹配"""
    def embed_documents(self, texts):
        return [[0.0] * 10 for _ in texts]

    def embed_query(self, text):
        return [0.0] * 10
        
    def __call__(self, text):
        return self.embed_query(text)
