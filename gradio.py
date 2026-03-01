"""
RAG 系统 Web 界面 - 集成记忆管理功能
"""
import os
import sys
import gradio as gr
from typing import Generator, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.rag_system import RAGSystem

# 全局 RAG 实例
rag = None


def initialize_rag():
    """初始化 RAG 系统"""
    global rag
    if rag is None:
        rag = RAGSystem()
        rag.initialize()
        # rag.process_documents()
    return rag


def query_rag_stream(question: str, k: int = 5, use_history: bool = True) -> Generator[str, None, None]:
    """流式查询 RAG 系统 - 真实推理渲染版本"""
    if not question.strip():
        yield "请输入问题", ""
        return
    
    # 获取相关文档提取来源
    retrieved_docs = rag.similarity_search(question, k=k)
    sources_text = ""
    if retrieved_docs:
        sources = set()
        for doc in retrieved_docs:
            if "source" in doc.metadata:
                sources.add(doc.metadata["source"])
        if sources:
            sources_text = "\n\n📚 来源:\n" + "\n".join([f"  • {s}" for s in sources])
            
    # 初始化界面
    yield "🤔 正在思考中...", sources_text
    
    thinking_buffer = ""
    answer_buffer = ""
    
    # 接收后端解析好的 (思考过程, 最终输出)
    for thinking_chunk, answer_chunk in rag.query_stream(question, k=k, use_history=use_history):
        thinking_buffer += thinking_chunk
        answer_buffer += answer_chunk
        
        # 动态组装 Markdown
        full_response = ""
        
        # 渲染思考过程：使用引用块（>）产生灰色、缩进的视觉效果
        if thinking_buffer.strip():
            # 保证每行都有 '>' 以维持 Markdown 引用格式
            formatted_thinking = "\n".join([f"> {line}" for line in thinking_buffer.split("\n")])
            full_response += f"🤔 **思考过程**：\n{formatted_thinking}\n\n"
        
        # 渲染最终输出
        if answer_buffer.strip():
            if full_response:
                full_response += "💡 **最终输出**：\n\n"
            full_response += answer_buffer
            
        yield full_response, sources_text

def query_rag(question: str, k: int = 5) -> Tuple[str, str]:
    """非流式查询 RAG 系统"""
    if not question.strip():
        return "请输入问题", ""
    
    result = rag.query(question, k=k)
    
    if "error" in result:
        return result["error"], ""
    
    answer = result["answer"]
    sources_text = ""
    
    if result.get("sources"):
        sources_text = "\n\n📚 来源:\n" + "\n".join([f"  • {s}" for s in result["sources"]])
    
    return answer, sources_text


# ==================== 记忆管理功能 ====================

def clear_memory() -> str:
    """清空对话记忆"""
    if rag is None:
        return "❌ RAG 系统未初始化"
    
    success = rag.clear_memory()
    if success:
        return "✅ 对话记忆已彻底清空"
    else:
        return "❌ 清空记忆失败"


def trim_memory(max_messages: int) -> str:
    """裁剪对话记忆"""
    if rag is None:
        return "❌ RAG 系统未初始化"
    
    if max_messages < 1:
        return "❌ 请输入有效的数字（至少为1）"
    
    remaining = rag.trim_memory(max_messages)
    return f"✂️ 记忆已裁剪，保留 {remaining} 条对话"


def get_memory_summary() -> str:
    """获取对话摘要"""
    if rag is None:
        return "❌ RAG 系统未初始化"
    
    summary = rag.get_memory_summary()
    return summary


def get_memory_stats() -> str:
    """获取记忆统计信息"""
    if rag is None:
        return "❌ RAG 系统未初始化"
    
    stats = rag.get_memory_stats()
    
    return f"""📊 记忆统计信息

会话 ID: {stats['session_id']}
存储类型: {stats['storage_type']}
总消息数: {stats['total_messages']}
用户消息: {stats['human_messages']}
AI 消息: {stats['ai_messages']}
最大限制: {stats['max_limit']}"""


def get_memory_history() -> str:
    """获取对话历史"""
    if rag is None:
        return "❌ RAG 系统未初始化"
    
    history = rag.get_memory_history()
    return history


def refresh_memory_info() -> Tuple[str, str]:
    """刷新记忆信息"""
    return get_memory_stats(), get_memory_history()


# 创建 Gradio 界面
with gr.Blocks(title="RAG 智能问答系统", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 RAG 智能问答系统
    
    基于 LangChain 构建的检索增强生成系统，支持对话记忆管理
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            # 主问答区域
            chat_output = gr.Markdown(label="回答")
            sources_output = gr.Markdown(label="来源")
            
            with gr.Row():
                question_input = gr.Textbox(
                    label="输入问题",
                    placeholder="请输入您的问题...",
                    lines=2
                )
            
            with gr.Row():
                k_slider = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="检索文档数量"
                )
                use_history_checkbox = gr.Checkbox(
                    label="使用对话历史",
                    value=True,
                    info="启用后，AI 会记住之前的对话内容"
                )
            
            with gr.Row():
                stream_btn = gr.Button("🚀 流式生成", variant="primary")
                normal_btn = gr.Button("📤 普通查询", variant="secondary")
                clear_btn = gr.Button("🗑️ 清空输出")
        
        with gr.Column(scale=1):
            # 记忆管理区域
            gr.Markdown("### 🧠 记忆管理")
            
            with gr.Tab("统计信息"):
                stats_output = gr.Textbox(
                    label="记忆统计",
                    lines=8,
                    interactive=False
                )
                refresh_stats_btn = gr.Button("🔄 刷新统计")
            
            with gr.Tab("对话历史"):
                history_output = gr.Textbox(
                    label="历史记录",
                    lines=10,
                    interactive=False
                )
                refresh_history_btn = gr.Button("🔄 刷新历史")
            
            with gr.Tab("记忆操作"):
                gr.Markdown("#### 清空记忆")
                clear_memory_btn = gr.Button("�️ 清空所有对话记忆", variant="stop")
                clear_result = gr.Textbox(label="操作结果", interactive=False)
                
                gr.Markdown("#### 裁剪记忆")
                trim_slider = gr.Slider(
                    minimum=1,
                    maximum=50,
                    value=10,
                    step=1,
                    label="保留消息数量"
                )
                trim_memory_btn = gr.Button("✂️ 裁剪记忆")
                trim_result = gr.Textbox(label="裁剪结果", interactive=False)
                
                gr.Markdown("#### 生成摘要")
                summary_btn = gr.Button("📝 生成对话摘要")
                summary_output = gr.Textbox(
                    label="摘要内容",
                    lines=6,
                    interactive=False
                )
    
    # 事件绑定
    stream_btn.click(
        fn=query_rag_stream,
        inputs=[question_input, k_slider, use_history_checkbox],
        outputs=[chat_output, sources_output]
    )
    
    normal_btn.click(
        fn=query_rag,
        inputs=[question_input, k_slider],
        outputs=[chat_output, sources_output]
    )
    
    clear_btn.click(
        fn=lambda: ("", ""),
        outputs=[chat_output, sources_output]
    )
    
    # 记忆管理事件绑定
    clear_memory_btn.click(
        fn=clear_memory,
        outputs=clear_result
    )
    
    trim_memory_btn.click(
        fn=trim_memory,
        inputs=trim_slider,
        outputs=trim_result
    )
    
    summary_btn.click(
        fn=get_memory_summary,
        outputs=summary_output
    )
    
    refresh_stats_btn.click(
        fn=get_memory_stats,
        outputs=stats_output
    )
    
    refresh_history_btn.click(
        fn=get_memory_history,
        outputs=history_output
    )
    
    # 页面加载时刷新记忆信息
    demo.load(
        fn=refresh_memory_info,
        outputs=[stats_output, history_output]
    )
    
    gr.Markdown("""
    ---
    ### 💡 使用提示
    
    1. **对话记忆**：系统会自动保存对话历史，AI 会记住之前的对话内容
    2. **Redis 存储**：配置环境变量 `USE_REDIS=true` 可启用 Redis 持久化存储
    3. **记忆管理**：
       - 当对话历史过长时，可以使用"裁剪记忆"功能保留最近的对话
       - 使用"生成摘要"功能快速了解对话的主要内容
       - 使用"清空记忆"功能重新开始新的对话
    4. **流式输出**：点击"流式生成"可以实时看到 AI 的思考过程和回答
    """)


if __name__ == "__main__":
    print("启动 RAG Web 界面...")
    print("正在初始化系统...")
    
    # 初始化 RAG 系统
    initialize_rag()
    
    print("系统初始化完成！")
    print("请在浏览器中访问 http://localhost:7860")
    
    # 启动 Gradio
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
