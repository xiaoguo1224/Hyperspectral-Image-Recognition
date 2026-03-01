from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os

from rag import get_config

app = Flask(__name__)

# 配置 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化 RAG 配置
config = get_config()
logger.info(f"RAG 配置加载完成：LLM={config.LLM_MODEL}, Embedding={config.EMBEDDING_MODEL}")
logger.info("RAG 系统将在第一次请求时自动初始化")

# 注册 RAG 蓝图
from rag.routes import rag_bp
app.register_blueprint(rag_bp)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/api/rag/health', methods=['GET'])
def rag_health():
    """RAG 系统健康检查"""
    try:
        from rag.routes import get_rag
        rag = get_rag()
        return jsonify({
            "status": "ok",
            "rag_initialized": True,
            "session_id": rag.session_id
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Flask 应用启动中...")
    logger.info("=" * 60)
    logger.info(f"RAG 配置：LLM={config.LLM_MODEL}, Embedding={config.EMBEDDING_MODEL}")
    logger.info("RAG 系统将在第一次请求时自动初始化")
    logger.info("")
    logger.info("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
