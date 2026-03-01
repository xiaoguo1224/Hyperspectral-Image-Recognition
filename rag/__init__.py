"""
RAG 系统包 - LangChain v1.2.x 生产级实现
基于 LangChain 最新 API + Redis 会话记忆 + 流式输出
"""
from .rag_system import RAGSystem
from .config import Config, get_config

__all__ = ['RAGSystem', 'Config', 'get_config']
