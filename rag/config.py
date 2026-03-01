"""
RAG 系统配置管理
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类"""

    # Ollama 配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    LLM_MODEL = os.getenv("LLM_MODEL")

    # 文档处理配置
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

    # 路径配置
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    PAPERS_DIR = os.path.join(BASE_DIR, "papers")
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")

    # Redis 配置
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"

    # 记忆配置
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    SESSION_ID = os.getenv("SESSION_ID", "default_session")

    # 确保目录存在
    os.makedirs(PAPERS_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)

    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("=" * 50)
        print("RAG 系统配置")
        print("=" * 50)
        print(f"Ollama 地址：{cls.OLLAMA_BASE_URL}")
        print(f"嵌入模型：{cls.EMBEDDING_MODEL}")
        print(f"LLM 模型：{cls.LLM_MODEL}")
        print(f"分块大小：{cls.CHUNK_SIZE}")
        print(f"分块重叠：{cls.CHUNK_OVERLAP}")
        print(f"论文目录：{cls.PAPERS_DIR}")
        print(f"数据库目录：{cls.DB_DIR}")
        print(f"Redis 地址：{cls.REDIS_URL}")
        print(f"使用 Redis：{cls.USE_REDIS}")
        print(f"最大历史消息数：{cls.MAX_HISTORY_MESSAGES}")
        print(f"会话 ID: {cls.SESSION_ID}")
        print("=" * 50)


def get_config() -> type:
    """获取配置类"""
    return Config
