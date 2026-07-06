"""Build the Chroma knowledge base from world_settings.txt."""

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

from app.core.config import settings
from app.core.rag_engine import DB_PATH, rag_engine

SOURCE_PATH = f"{settings.ROOT_DIR}/app/data/world_settings.txt"


def build_knowledge_base() -> None:
    print("[RAG] Building knowledge base...")

    loader = TextLoader(SOURCE_PATH, encoding="utf-8")
    documents = loader.load()

    splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    print(f"[RAG] Split into {len(chunks)} chunks")

    Chroma.from_documents(
        documents=chunks,
        embedding=rag_engine.embeddings,
        persist_directory=DB_PATH,
    )
    print(f"[RAG] Persisted to: {DB_PATH}")


if __name__ == "__main__":
    build_knowledge_base()
