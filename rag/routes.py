"""
RAG 系统 API 路由 - 基于 RAGSystem 单例实现（按需初始化）
"""
import os
import json
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from typing import Generator, Optional

from .rag_system import RAGSystem
from .config import Config

logger = logging.getLogger(__name__)

# 创建蓝图
rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')

# 全局 RAG 单例
_rag_instance: Optional[RAGSystem] = None
_rag_initializing = False


def get_rag() -> RAGSystem:
    """
    获取或创建 RAG 系统单例（按需自动初始化）
    
    Returns:
        RAGSystem: RAG 系统实例
        
    Raises:
        RuntimeError: 初始化失败时抛出
    """
    global _rag_instance, _rag_initializing
    
    # 如果已经初始化完成，直接返回
    if _rag_instance and hasattr(_rag_instance, '_initialized') and _rag_instance._initialized:
        return _rag_instance
    
    # 如果正在初始化中，等待一下
    if _rag_initializing:
        import time
        for _ in range(30):  # 最多等待 30 秒（给文档处理留出时间）
            time.sleep(1)
            if _rag_instance and hasattr(_rag_instance, '_initialized') and _rag_instance._initialized:
                return _rag_instance
        raise RuntimeError("RAG 系统初始化超时，请检查服务状态")
    
    # 开始初始化
    _rag_initializing = True
    try:
        logger.info("开始初始化 RAG 系统...")
        
        # 创建 RAG 系统实例
        _rag_instance = RAGSystem()
        
        # 标记为已初始化
        _rag_instance._initialized = True
        
        logger.info("✓ RAG 系统初始化完成")
        return _rag_instance
        
    except Exception as e:
        logger.error(f"RAG 系统初始化失败：{e}")
        raise
    finally:
        _rag_initializing = False

get_rag()

# ==================== 核心查询接口 ====================

@rag_bp.route('/query/stream', methods=['POST'])
def query_stream():
    """
    流式查询接口 (SSE) - 实时返回思考过程和答案
    
    请求体:
    {
        "question": "用户问题",
        "k": 5,                    // 可选，检索的文档数量，默认 5
        "use_history": true        // 可选，是否使用对话历史，默认 true
    }
    
    响应：SSE 流
    - data: {"type": "sources", "content": ["来源 1", "来源 2"]}
    - data: {"type": "thinking", "content": "思考过程片段"}
    - data: {"type": "answer", "content": "答案片段"}
    - data: {"type": "done"}
    """
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"code": 400, "error": "缺少必要参数：question"}), 400
        
        question = data['question']
        k = data.get('k', 5)
        use_history = data.get('use_history', True)
        
        # 获取 RAG 实例（自动初始化）
        rag = get_rag()
        
        def generate() -> Generator[str, None, None]:
            """生成 SSE 流"""
            try:
                # 获取相关文档
                retrieved_docs = rag.similarity_search(question, k=k)
                sources = list(set([
                    doc.metadata.get('source', '未知来源')
                    for doc in retrieved_docs
                ]))
                
                # 发送来源信息
                yield f"data: {json.dumps({'type': 'sources', 'content': sources}, ensure_ascii=False)}\n\n"
                
                # 流式生成答案
                for thinking_text, response_text in rag.query_stream(question, k=k, use_history=use_history):
                    # 发送思考过程
                    if thinking_text:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': thinking_text}, ensure_ascii=False)}\n\n"
                    
                    # 发送答案内容
                    if response_text:
                        yield f"data: {json.dumps({'type': 'answer', 'content': response_text}, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"流式生成错误：{e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"流式查询接口错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


# ==================== 文档检索接口 ====================

@rag_bp.route('/search', methods=['POST'])
def search():
    """
    文档检索接口 - 直接返回相关文档片段
    
    请求体:
    {
        "query": "搜索查询",
        "k": 5                    // 可选，返回的文档数量，默认 5
    }
    
    响应:
    {
        "code": 200,
        "data": {
            "query": "搜索查询",
            "results": [
                {
                    "content": "文档内容",
                    "metadata": {"source": "来源", ...}
                }
            ],
            "count": 5
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"code": 400, "error": "缺少必要参数：query"}), 400
        
        query = data['query']
        k = data.get('k', 5)
        
        # 获取 RAG 实例
        rag = get_rag()
        docs = rag.similarity_search(query, k=k)
        
        results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]
        
        return jsonify({
            "code": 200,
            "data": {
                "query": query,
                "results": results,
                "count": len(results)
            }
        })
        
    except Exception as e:
        logger.error(f"搜索接口错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


# ==================== 文档管理接口 ====================

@rag_bp.route('/documents/process', methods=['POST'])
def process_documents():
    """
    处理文档接口 - 重新处理所有文档并构建向量存储
    
    请求体：无
    
    响应:
    {
        "code": 200,
        "message": "成功处理 X 个文档",
        "data": {
            "document_count": 10
        }
    }
    
    注意：
    - 如果向量存储已有数据，会跳过处理
    - 如需强制重新处理，请先调用 /documents/rebuild
    """
    try:
        # 获取 RAG 实例
        rag = get_rag()
        
        # 处理文档
        documents = rag.process_documents()
        
        return jsonify({
            "code": 200,
            "message": f"成功处理 {len(documents)} 个文档",
            "data": {
                "document_count": len(documents)
            }
        })
        
    except Exception as e:
        logger.error(f"处理文档错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


@rag_bp.route('/documents/rebuild', methods=['POST'])
def rebuild_documents():
    """
    重建文档索引 - 强制删除并重新构建向量存储
    
    请求体：无
    
    响应:
    {
        "code": 200,
        "message": "成功重建向量存储",
        "data": {
            "document_count": 10
        }
    }
    
    注意：
    - 会删除现有的向量存储
    - 重新处理所有文档
    - 耗时较长，请谨慎使用
    """
    try:
        global _rag_instance
        
        # 删除旧的向量存储
        if os.path.exists(Config.DB_DIR):
            import shutil
            shutil.rmtree(Config.DB_DIR)
            logger.info(f"已删除旧向量存储：{Config.DB_DIR}")
        
        # 重置 RAG 实例
        _rag_instance = None
        
        # 重新初始化
        rag = get_rag()
        
        # 强制处理文档
        documents = rag.process_documents()
        
        return jsonify({
            "code": 200,
            "message": "成功重建向量存储",
            "data": {
                "document_count": len(documents)
            }
        })
        
    except Exception as e:
        logger.error(f"重建文档索引错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


# ==================== 记忆管理接口 ====================

@rag_bp.route('/memory/clear', methods=['POST'])
def clear_memory():
    """
    清空对话记忆接口
    
    请求体：无
    
    响应:
    {
        "code": 200,
        "message": "对话记忆已清空"
    }
    """
    try:
        # 获取 RAG 实例
        rag = get_rag()
        success = rag.clear_memory()
        
        return jsonify({
            "code": 200,
            "message": "对话记忆已清空" if success else "清空失败"
        })
        
    except Exception as e:
        logger.error(f"清空记忆错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


@rag_bp.route('/memory/stats', methods=['GET'])
def memory_stats():
    """
    获取记忆统计信息
    
    请求参数：无
    
    响应:
    {
        "code": 200,
        "data": {
            "message_count": 10,
            "session_id": "会话 ID",
            ...
        }
    }
    """
    try:
        # 获取 RAG 实例
        rag = get_rag()
        stats = rag.get_memory_stats()
        
        return jsonify({
            "code": 200,
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"获取记忆统计错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


@rag_bp.route('/memory/history', methods=['GET'])
def memory_history():
    """
    获取对话历史记录
    
    请求参数：无
    
    响应:
    {
        "code": 200,
        "data": {
            "history": "格式化的历史对话",
            "session_id": "会话 ID"
        }
    }
    """
    try:
        # 获取 RAG 实例
        rag = get_rag()
        history = rag.get_memory_history()
        
        return jsonify({
            "code": 200,
            "data": {
                "history": history,
                "session_id": rag.session_id
            }
        })
        
    except Exception as e:
        logger.error(f"获取对话历史错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


# ==================== 系统管理接口 ====================

@rag_bp.route('/status', methods=['GET'])
def system_status():
    """
    获取系统状态信息
    
    请求参数：无
    
    响应:
    {
        "code": 200,
        "data": {
            "initialized": true,
            "session_id": "会话 ID",
            "ollama_url": "http://localhost:11434",
            "llm_model": "qwen3:8b",
            "embedding_model": "qwen3-embedding:0.6b",
            "vector_store": {
                "total_documents": 10,
                ...
            },
            "memory": {
                "message_count": 5,
                ...
            }
        }
    }
    """
    try:
        # 获取 RAG 实例
        rag = get_rag()
        stats = {
            "initialized": True,
            "session_id": rag.session_id,
            "ollama_url": Config.OLLAMA_BASE_URL,
            "llm_model": Config.LLM_MODEL,
            "embedding_model": Config.EMBEDDING_MODEL
        }
        
        # 添加向量存储统计
        if rag.vector_store and rag.vector_store.db:
            vector_stats = rag.vector_store.get_stats()
            stats["vector_store"] = vector_stats
        
        # 添加记忆统计
        memory_stats = rag.get_memory_stats()
        stats["memory"] = memory_stats
        
        return jsonify({
            "code": 200,
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"获取系统状态错误：{e}")
        return jsonify({"code": 500, "error": str(e)}), 500


@rag_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    请求参数：无
    
    响应:
    {
        "code": 200,
        "data": {
            "status": "ok",
            "message": "RAG 系统运行正常"
        }
    }
    """
    try:
        # 检查 RAG 系统是否可初始化
        rag = get_rag()
        return jsonify({
            "code": 200,
            "data": {
                "status": "ok",
                "message": "RAG 系统运行正常",
                "session_id": rag.session_id
            }
        })
    except Exception as e:
        logger.error(f"健康检查失败：{e}")
        return jsonify({
            "code": 500,
            "data": {
                "status": "error",
                "message": str(e)
            }
        }), 500
