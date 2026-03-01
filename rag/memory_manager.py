"""
记忆管理模块 - 集成 Redis 存储、记忆裁剪、摘要总结和清空功能
参考项目：F:\A____usually\code\ProjectCode\langchain\chat_system.py
"""
import os
from typing import Optional, List

import json
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import trim_messages, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from .config import Config


class MemoryManager:
    """
    记忆管理器 - 管理对话历史的存储、裁剪、摘要和清空

    功能：
    1. Redis 记忆存储 - 支持 Redis 持久化和内存存储
    2. 记忆裁剪 - 基于消息数量的安全裁剪
    3. 对话摘要总结 - 使用 LLM 生成对话摘要
    4. 记忆清空 - 安全清空所有历史记录
    """

    def __init__(self, session_id: str = None, use_redis: bool = None):
        """
        初始化记忆管理器

        Args:
            session_id: 会话ID，用于区分不同对话
            use_redis: 是否使用Redis存储，默认从配置读取
        """
        self.session_id = session_id or Config.SESSION_ID
        self.use_redis = use_redis if use_redis is not None else Config.USE_REDIS
        self.redis_url = Config.REDIS_URL
        self.max_messages = Config.MAX_HISTORY_MESSAGES

        # 全局会话存储（用于内存模式）
        self._memory_store = {}

        # 初始化历史记录
        self._history = self._get_or_create_history()

    def _get_or_create_history(self) -> BaseChatMessageHistory:
        """
        获取或创建历史记录对象

        Returns:
            BaseChatMessageHistory: 历史记录对象
        """
        if self.session_id not in self._memory_store:
            if self.use_redis:
                try:
                    self._memory_store[self.session_id] = RedisChatMessageHistory(
                        session_id=self.session_id,
                        url=self.redis_url
                    )
                    print(f"✅ Redis 记忆存储已连接: {self.session_id}")
                except Exception as e:
                    print(f"⚠️ Redis 连接失败，切换到内存存储: {e}")
                    self._memory_store[self.session_id] = InMemoryChatMessageHistory()
                    self.use_redis = False
            else:
                self._memory_store[self.session_id] = InMemoryChatMessageHistory()
                print(f"✅ 内存记忆存储已创建: {self.session_id}")

        return self._memory_store[self.session_id]

    @property
    def history(self) -> BaseChatMessageHistory:
        """获取当前历史记录对象"""
        return self._history

    def add_user_message(self, content: str):
        """添加用户消息"""
        self._history.add_user_message(content)

    def add_ai_message(self, content: str):
        """添加 AI 消息"""
        self._history.add_ai_message(content)

    def get_messages(self) -> List:
        """获取所有消息列表"""
        return self._history.messages

    def clear(self) -> bool:
        """
        清空所有历史记录

        Returns:
            bool: 是否成功清空
        """
        try:
            self._history.clear()
            print(f"🧹 会话 '{self.session_id}' 的记忆已彻底清空")
            return True
        except Exception as e:
            print(f"❌ 清空记忆失败: {e}")
            return False

    def trim(self, max_messages: int = None) -> int:
        """
        安全裁剪历史记录，保留最新的消息

        Args:
            max_messages: 最大保留消息数，默认从配置读取

        Returns:
            int: 裁剪后剩余的消息数
        """
        max_msgs = max_messages or self.max_messages
        messages = self._history.messages

        if len(messages) <= max_msgs:
            print(f"✅ 当前消息数({len(messages)})未超过限制({max_msgs})，无需裁剪")
            return len(messages)

        # 使用 LangChain 标准的 trimmer 工具
        trimmer = trim_messages(
            max_tokens=max_msgs,
            strategy="last",          # 保留最新的消息
            token_counter=len,        # 按消息条数计算
            start_on="human",         # 确保裁剪后以人类消息开头
            allow_partial=False
        )

        # 执行裁剪
        trimmed_messages = trimmer.invoke(messages)

        # 更新存储
        self._history.clear()
        for msg in trimmed_messages:
            self._history.add_message(msg)

        print(f"记忆已安全裁剪: {len(messages)} -> {len(trimmed_messages)} 条")
        return len(trimmed_messages)

    def get_summary(self, llm: ChatOllama = None) -> str:
        """
        生成对话摘要

        Args:
            llm: LLM 实例，用于生成摘要

        Returns:
            str: 对话摘要
        """
        messages = self._history.messages

        if not messages:
            return "暂无对话内容可供总结"

        if llm is None:
            llm = ChatOllama(
                model=Config.LLM_MODEL,
                base_url=Config.OLLAMA_BASE_URL,
                temperature=0.7
            )

        # 将历史消息格式化为文本
        history_text = "\n".join([
            f"[{'用户' if msg.type == 'human' else 'AI'}]: {msg.content[:200]}..."
            if len(msg.content) > 200 else f"[{'用户' if msg.type == 'human' else 'AI'}]: {msg.content}"
            for msg in messages
        ])

        # 构建摘要提示词
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个精通信息提取的 AI 助手。请客观、简练地概括对话的核心要点。"),
            ("human", "请总结以下对话的主要内容：\n\n{history_text}\n\n摘要：")
        ])

        summary_chain = summary_prompt | llm

        try:
            result = summary_chain.invoke({"history_text": history_text})
            return result.content
        except Exception as e:
            return f"生成摘要失败: {e}"

    def get_stats(self) -> dict:
        """
        获取记忆统计信息

        Returns:
            dict: 统计信息
        """
        messages = self._history.messages
        human_count = sum(1 for msg in messages if msg.type == "human")
        ai_count = sum(1 for msg in messages if msg.type == "ai")

        return {
            "session_id": self.session_id,
            "storage_type": "Redis" if self.use_redis else "Memory",
            "total_messages": len(messages),
            "human_messages": human_count,
            "ai_messages": ai_count,
            "max_limit": self.max_messages
        }

    def format_history_for_display(self) -> str:
        """
        格式化历史记录用于前端显示 (返回 JSON 字符串以供前端精准解析)

        Returns:
            str: JSON 格式的字符串，或者空状态提示
        """
        messages = self._history.messages

        if not messages:
            return "暂无对话记录"

        history_list = []
        for msg in messages:
            # 仅提取前端需要的 user (human) 和 ai 消息，忽略 system 提示词等
            if msg.type in ["human", "AIMessageChunk"]:
                history_list.append({
                    "type": "human" if msg.type=="human" else "ai",
                    "content": msg.content
                })

        # 将其序列化为 JSON 字符串返回 (ensure_ascii=False 保证中文正常显示)
        return json.dumps(history_list, ensure_ascii=False)


# 全局记忆管理器实例（单例模式）
_memory_manager_instance = None


def get_memory_manager(session_id: str = None, use_redis: bool = None) -> MemoryManager:
    """
    获取记忆管理器实例（工厂函数）

    Args:
        session_id: 会话ID
        use_redis: 是否使用Redis

    Returns:
        MemoryManager: 记忆管理器实例
    """
    global _memory_manager_instance

    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager(session_id, use_redis)

    return _memory_manager_instance


def reset_memory_manager():
    """重置记忆管理器实例"""
    global _memory_manager_instance
    _memory_manager_instance = None


if __name__ == "__main__":
    # 测试代码
    print("=== 记忆管理器测试 ===\n")

    # 创建记忆管理器（内存模式）
    memory = MemoryManager(session_id="test_session", use_redis=False)

    # 添加测试消息
    memory.add_user_message("你好，我想了解高光谱图像")
    memory.add_ai_message("你好！高光谱图像是一种包含连续窄波段光谱信息的图像...")
    memory.add_user_message("它有什么应用场景？")
    memory.add_ai_message("高光谱图像主要应用于农业监测、环境监测、军事侦察等领域...")

    # 显示统计
    print("统计信息:", memory.get_stats())
    print("\n历史记录:")
    print(memory.format_history_for_display())

    # 测试摘要
    print("\n对话摘要:")
    print(memory.get_summary())

    # 测试裁剪
    print("\n测试裁剪:")
    memory.trim(max_messages=2)
    print("裁剪后统计:", memory.get_stats())

    # 测试清空
    print("\n测试清空:")
    memory.clear()
    print("清空后统计:", memory.get_stats())
