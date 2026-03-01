import os
from rag.config import Config

from rag.document_processor import DocumentProcessor
from rag.vector_store import VectorStore


def process_documents():
    processor = DocumentProcessor(Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
    vector_store = VectorStore(
        Config.DB_DIR,
        Config.EMBEDDING_MODEL,
        Config.OLLAMA_BASE_URL
    )
    """处理文档并构建向量存储"""
    print("\n" + "=" * 50)
    print("处理文档")
    print("=" * 50)

    # 检查是否有 PDF 文件
    pdf_count = len([f for f in os.listdir(Config.PAPERS_DIR) if f.endswith(".pdf")])

    if pdf_count > 0:
        print(f"找到 {pdf_count} 个 PDF 文件")
        documents = processor.process_papers(Config.PAPERS_DIR)
    else:
        print("未找到 PDF 文件，创建示例文档...")
        documents = processor.create_sample_documents(Config.PAPERS_DIR)

    # 添加到向量存储
    print("\n构建向量存储 (执行 Embedding)...")
    vector_store.create_vectorstore(documents)

    stats = vector_store.get_stats()
    print(f"\n向量存储统计：{stats['total_documents']} 个文档")

    # 测试
    results = vector_store.similarity_search(
        "What is the main contribution of the paper?",
        k=5
    )
    for doc in results:
        print(f"* {doc.page_content} [{doc.metadata}]")
    return documents

if __name__ == '__main__':
    Config.print_config()
    process_documents()