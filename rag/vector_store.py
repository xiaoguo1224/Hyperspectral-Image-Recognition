"""
向量存储模块 - 使用 LangChain 和 ChromaDB
"""
import os
from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma


class VectorStore:
    """向量存储类 - LangChain 版本"""

    def __init__(self, db_path: str, embedding_model: str, ollama_url: str):
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.ollama_url = ollama_url

        # 使用 LangChain 的 Ollama 嵌入
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=ollama_url
        )

        # 初始化 ChromaDB 向量存储
        self.db = None

    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """从文档创建向量存储"""
        if not documents:
            print("没有文档可添加")
            return None

        print(f"正在创建向量存储，共 {len(documents)} 个文档...")

        # 使用 LangChain 的 Chroma 集成
        self.db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.db_path,
            collection_name="papers_collection"
        )

        # 持久化
        # self.db.persist()

        print(f"向量存储创建完成，保存在: {self.db_path}")
        return self.db

    def load_vectorstore(self) -> Optional[Chroma]:
        """加载已有的向量存储"""
        if not os.path.exists(self.db_path):
            print(f"向量存储不存在: {self.db_path}")
            return None

        try:
            self.db = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings,
                collection_name="papers_collection"
            )
            print(f"向量存储加载成功")
            return self.db
        except Exception as e:
            print(f"加载向量存储失败: {e}")
            return None

    def add_documents(self, documents: List[Document]):
        """添加文档到向量存储"""
        if not documents:
            print("没有文档可添加")
            return

        if self.db is None:
            # 如果数据库不存在，创建新的
            self.create_vectorstore(documents)
        else:
            # 添加到现有数据库
            print(f"添加 {len(documents)} 个文档到向量存储...")
            self.db.add_documents(documents)
            self.db.persist()
            print("文档添加完成")

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """相似性搜索"""
        if self.db is None:
            print("向量存储未初始化")
            return []

        # 使用 LangChain 的相似性搜索
        results = self.db.similarity_search(query, k=k)
        return results

    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """带分数的相似性搜索"""
        if self.db is None:
            print("向量存储未初始化")
            return []

        # 使用 LangChain 的相似性搜索（带分数）
        results = self.db.similarity_search_with_score(query, k=k)
        return results

    def get_retriever(self, search_kwargs: Dict = None):
        """获取 LangChain 检索器"""
        if self.db is None:
            print("向量存储未初始化")
            return None

        kwargs = search_kwargs or {"k": 5}
        return self.db.as_retriever(search_kwargs=kwargs)

    def get_stats(self) -> Dict:
        """获取向量存储统计信息"""
        if self.db is None:
            return {"total_documents": 0, "db_path": self.db_path}

        try:
            # 获取集合中的文档数量
            count = self.db._collection.count()
            return {
                "total_documents": count,
                "db_path": self.db_path,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            return {"total_documents": 0, "db_path": self.db_path, "error": str(e)}

    def clear(self):
        """清空向量存储"""
        if self.db is not None:
            # 删除集合中的所有文档
            try:
                self.db.delete_collection()
                print("向量存储已清空")
            except Exception as e:
                print(f"清空向量存储失败: {e}")

        # 重新初始化
        self.db = None


if __name__ == "__main__":
    from config import Config

    store = VectorStore(Config.DB_DIR, Config.EMBEDDING_MODEL, Config.OLLAMA_BASE_URL)

    # 尝试加载现有存储
    db = store.load_vectorstore()

    if db:
        stats = store.get_stats()
        print(f"向量存储统计: {stats}")
    else:
        print("向量存储不存在，请先添加文档")
