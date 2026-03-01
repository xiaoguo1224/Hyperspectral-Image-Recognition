"""
RAG 主系统 - 使用 LangChain 整合所有组件 (集成记忆功能)
"""
import os
from typing import List, Dict, Optional, Generator, AsyncGenerator
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory

from rag.config import Config
from rag.document_processor import DocumentProcessor
from rag.vector_store import VectorStore
from rag.memory_manager import MemoryManager, get_memory_manager

from typing import Generator, Tuple

# 自定义 RAG Prompt 模板 - 包含对话历史
RAG_PROMPT_TEMPLATE = """基于以下上下文信息回答问题。如果上下文中没有相关信息，那你可以根据自己的知识来回答，但不要编造答案。

上下文：
{context}

当前问题：{input}

请用中文详细回答："""

RAG_PROMPT_WITH_HISTORY = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的 AI 助手，基于提供的上下文信息回答问题。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", """基于以下上下文回答问题：

上下文：
{context}

问题：{input}

请用中文详细回答：""")
])


def format_docs(docs: List[Document]) -> str:
    """格式化文档列表为字符串"""
    return "\n\n".join([f"[文档{i + 1}] {doc.page_content}" for i, doc in enumerate(docs)])


class RAGSystem:
    """RAG 系统主类 - 集成记忆功能"""

    def __init__(self, session_id: str = None, use_redis: bool = None):
        self.config = Config
        self.vector_store = None
        self.processor = DocumentProcessor(Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
        self.llm = None
        self.rag_chain = None
        self.rag_chain_with_history = None

        # 初始化记忆管理器
        self.memory_manager = get_memory_manager(session_id, use_redis)
        self.session_id = self.memory_manager.session_id

        self.initialize()

        # self.process_documents()
        # 打印配置
        Config.print_config()

    def initialize(self):
        """初始化系统"""
        print("\n初始化 RAG 系统...")

        # 检查 Ollama 是否运行
        if not self._check_ollama():
            print("警告：Ollama 服务未运行，请先启动 Ollama")
            return False
        # 初始化流式 LLM
        self.llm = ChatOllama(
            model=Config.LLM_MODEL,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=0.7,
            reasoning=True
        )

        # 初始化向量存储
        self.vector_store = VectorStore(
            Config.DB_DIR,
            Config.EMBEDDING_MODEL,
            Config.OLLAMA_BASE_URL
        )

        # 尝试加载已有向量存储
        self.vector_store.load_vectorstore()

        print("RAG 系统初始化完成\n")
        return True

    def _check_ollama(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            import requests
            response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _create_rag_chain(self, use_history: bool = False, k=5):
        """创建 LangChain RAG 链 (LCEL 风格)"""
        if self.vector_store.db is None:
            print("向量存储未初始化")
            return None

        # 获取检索器
        retriever = self.vector_store.get_retriever(search_kwargs={"k": k})

        # 选择 LLM
        llm = self.llm

        if use_history:
            base_chain = (
                    {
                        "context": lambda x: format_docs(retriever.invoke(x["input"])),
                        "input": lambda x: x["input"],
                        "history": lambda x: x.get("history", [])
                    }
                    | RAG_PROMPT_WITH_HISTORY
                    | llm
            )
        else:
            base_chain = (
                    {
                        "context": retriever | format_docs,
                        "input": RunnablePassthrough()
                    }
                    | ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
                    | llm
            )

        if use_history:
            rag_chain = RunnableWithMessageHistory(
                base_chain,
                lambda session_id: self.memory_manager.history,
                input_messages_key="input",
                history_messages_key="history",
            )
            return rag_chain

        return base_chain

    def process_documents(self):
        """处理文档并构建向量存储"""
        print("\n" + "=" * 50)
        print("处理文档")
        print("=" * 50)

        # 检查是否有 PDF 文件
        pdf_count = len([f for f in os.listdir(Config.PAPERS_DIR) if f.endswith(".pdf")])

        if pdf_count > 0:
            print(f"找到 {pdf_count} 个 PDF 文件")
            documents = self.processor.process_papers(Config.PAPERS_DIR)
        else:
            print("未找到 PDF 文件，创建示例文档...")
            documents = self.processor.create_sample_documents(Config.PAPERS_DIR)

        # 添加到向量存储
        print("\n构建向量存储 (执行 Embedding)...")
        self.vector_store.create_vectorstore(documents)

        stats = self.vector_store.get_stats()
        print(f"\n向量存储统计：{stats['total_documents']} 个文档")

        return documents

    def query_stream(self, question: str, k: int = 5, use_history: bool = True) -> Generator[
        tuple[str, str], None, None]:
        """流式查询 RAG 系统 - 提取真实的思考过程"""
        if not self.vector_store or not self.vector_store.db:
            yield "", "错误：系统未初始化或向量存储为空"
            return

        # 创建流式 RAG 链
        streaming_chain = self._create_rag_chain(use_history=use_history, k=k)

        if streaming_chain is None:
            yield "", "错误：无法创建 RAG 链"
            return

        try:
            answer_buffer = ""
            if use_history:
                config = {"configurable": {"session_id": self.session_id}}
                stream_iter = streaming_chain.stream({"input": question}, config=config)
            else:
                stream_iter = streaming_chain.stream(question)  # 根据 Passthrough，输入可能需要是字符串

            is_thinking = False

            for chunk in stream_iter:
                thinking_text = ""
                response_text = ""

                # 1. 尝试从 additional_kwargs 提取 (适配 DeepSeek API、vLLM 等)
                if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs.get("reasoning_content"):
                    thinking_text = chunk.additional_kwargs.get("reasoning_content", "")
                    response_text = chunk.content if hasattr(chunk, 'content') else ""

                # 2. 尝试从 content 解析 <think> 标签 (适配 Ollama 本地的 DeepSeek-R1)
                else:
                    content_text = chunk.content if hasattr(chunk, 'content') else str(chunk)

                    if "<think>" in content_text:
                        is_thinking = True
                        content_text = content_text.replace("<think>", "")

                    if "</think>" in content_text:
                        is_thinking = False
                        parts = content_text.split("</think>")
                        thinking_text = parts[0]
                        response_text = parts[1] if len(parts) > 1 else ""
                    else:
                        if is_thinking:
                            thinking_text = content_text
                        else:
                            response_text = content_text

                # 仅将最终输出保存为文本（可选）
                answer_buffer += response_text

                # 将拆分好的思考与正文以元组返回
                yield thinking_text, response_text

            # 备注：使用 RunnableWithMessageHistory 时会自动保存记录，不用重复添加
            if not use_history:
                self.memory_manager.add_user_message(question)
                self.memory_manager.add_ai_message(answer_buffer)

        except Exception as e:
            yield "", f"\n查询失败: {str(e)}"

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """相似性搜索（直接返回文档）"""
        if not self.vector_store or not self.vector_store.db:
            return []

        return self.vector_store.similarity_search(query, k=k)

    # ==================== 记忆管理功能 ====================

    def clear_memory(self) -> bool:
        """清空对话记忆"""
        return self.memory_manager.clear()

    def trim_memory(self, max_messages: int = None) -> int:
        """裁剪对话记忆"""
        return self.memory_manager.trim(max_messages)

    def get_memory_summary(self) -> str:
        """获取对话摘要"""
        return self.memory_manager.get_summary(self.llm)

    def get_memory_stats(self) -> dict:
        """获取记忆统计信息"""
        return self.memory_manager.get_stats()

    def get_memory_history(self) -> str:
        """获取格式化的历史记录"""
        return self.memory_manager.format_history_for_display()

    def build(self):
        """完整构建流程"""
        print("\n" + "=" * 60)
        print("RAG 系统构建流程")
        print("=" * 60)

        # 初始化
        if not self.initialize():
            print("初始化失败，请检查 Ollama 服务")
            return

        # 爬取论文
        # self.crawl_papers()

        # 处理文档
        self.process_documents()

        print("\n" + "=" * 60)
        print("RAG 系统构建完成！")
        print("=" * 60)
        print("\n现在可以使用 query() 或 chat() 方法进行查询")
        print("示例：rag.query('高光谱显著目标检测的主要方法有哪些？')")
        self.query_stream(question="高光谱显著目标检测的主要方法有哪些？")


if __name__ == "__main__":
    rag = RAGSystem()
    rag.build()
