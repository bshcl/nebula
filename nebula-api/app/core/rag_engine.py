from langchain_huggingface import HuggingFaceEmbeddings  # 👈 换成这个
from langchain_chroma import Chroma
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/chroma_db")

class RAGEngine:
    def __init__(self):
        # 💡 架构师提示：使用本地模型，不再依赖 Google API，彻底解决 404
        # 第一次运行会自动下载模型文件（约 80MB）
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = None

    def get_vector_db(self):
        if self.vector_db is None:
            if not os.path.exists(DB_PATH):
                return None
            self.vector_db = Chroma(
                persist_directory=DB_PATH, embedding_function=self.embeddings
            )
        return self.vector_db

    def get_retriever(self, k=2):
        db = self.get_vector_db()
        if not db:
            return None
        return db.as_retriever(search_kwargs={"k": k})


rag_engine = RAGEngine()
