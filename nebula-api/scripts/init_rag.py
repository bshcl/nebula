from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from app.core.rag_engine import rag_engine, DB_PATH


def build_knowledge_base():
    print("🚀 [RAG Factory] 开始构建知识库...")

    # 1. 加载原始文档
    source_path = "./app/data/world_settings.txt"
    loader = TextLoader(source_path, encoding="utf-8")
    documents = loader.load()

    # 2. 智能切片
    # chunk_size: 碎片大小 | chunk_overlap: 重叠度（保证上下文不丢失）
    text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"📦 文档已切分为 {len(chunks)} 个碎片")

    # 3. 向量化并持久化到本地
    from langchain_chroma import Chroma

    Chroma.from_documents(
        documents=chunks, embedding=rag_engine.embeddings, persist_directory=DB_PATH
    )
    print(f"✅ 知识库已成功持久化至: {DB_PATH}")


if __name__ == "__main__":
    build_knowledge_base()
