"""Local Chroma vector store for world-setting RAG."""

import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

# Kept for scripts/init_rag.py
DB_PATH = os.path.join(settings.ROOT_DIR, "app", "data", "chroma_db")

EMBEDDING_MODEL = settings.EMBEDDING_MODEL


class RAGEngine:
    """Lazy-loaded Chroma retriever backed by local HuggingFace embeddings."""

    def __init__(self) -> None:
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_db: Chroma | None = None

    def get_vector_db(self) -> Chroma | None:
        if self.vector_db is None:
            if not os.path.exists(DB_PATH):
                return None
            self.vector_db = Chroma(
                persist_directory=DB_PATH, embedding_function=self.embeddings
            )
        return self.vector_db

    def get_retriever(self, k: int = 2):
        db = self.get_vector_db()
        if not db:
            return None
        return db.as_retriever(search_kwargs={"k": k})


rag_engine = RAGEngine()
