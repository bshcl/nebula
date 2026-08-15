"""Local Chroma vector store for world-setting RAG."""

import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

# Kept for scripts/init_rag.py
DB_PATH = os.path.join(settings.VAR_DIR, "chroma_db")

EMBEDDING_MODEL = settings.EMBEDDING_MODEL


class RAGEngine:
    """Lazy-loaded Chroma retriever backed by local HuggingFace embeddings."""

    def __init__(self, persist_dir: str = DB_PATH, embedding_model: str = EMBEDDING_MODEL) -> None:
        self.persist_dir = persist_dir
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vector_db: Chroma | None = None

    def get_vector_db(self) -> Chroma | None:
        if self.vector_db is None:
            if not os.path.exists(self.persist_dir):
                return None
            self.vector_db = Chroma(
                persist_directory=self.persist_dir, embedding_function=self.embeddings
            )
        return self.vector_db

    def get_retriever(self, k: int = 2):
        db = self.get_vector_db()
        if not db:
            return None
        return db.as_retriever(search_kwargs={"k": k})


rag_engine = RAGEngine()
