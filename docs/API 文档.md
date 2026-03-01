# RAG 系统 API 文档

## 概述

本文档描述了 RAG（检索增强生成）系统的 RESTful API 接口。该系统基于 LangChain + ChromaDB + Ollama 构建，支持流式输出、对话历史管理和文档检索功能。

### 基本信息

- **Base URL**: `http://localhost:5000/api/rag`
- **认证方式**: 暂无（所有接口公开访问）
- **数据格式**: JSON
- **字符编码**: UTF-8

### 技术栈

- **框架**: Flask
- **向量数据库**: ChromaDB
- **LLM**: Ollama (qwen3:8b)
- **Embedding**: Ollama (qwen3-embedding:0.6b)
- **会话记忆**: Redis / 内存存储

---

## 错误处理机制

所有 API 响应均采用统一的响应格式：

### 成功响应

```json
{
  "code": 200,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "code": 400,  // 或其他错误码
  "error": "错误描述信息"
}
```

### HTTP 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

---

## API 接口列表

### 1. 核心查询接口

#### 1.1 流式查询接口

**端点**: `POST /api/rag/query/stream`

**描述**: 实时流式返回 RAG 查询结果，包含思考过程和答案片段。使用 SSE (Server-Sent Events) 协议。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| question | string | 是 | - | 用户问题 |
| k | integer | 否 | 5 | 检索的文档数量 |
| use_history | boolean | 否 | true | 是否使用对话历史 |

**请求示例**:

```json
{
  "question": "高光谱显著目标检测的主要方法有哪些？",
  "k": 5,
  "use_history": true
}
```

**响应格式**: SSE 流

```
data: {"type": "sources", "content": ["paper1.pdf", "paper2.pdf"]}

data: {"type": "thinking", "content": "首先需要分析高光谱..."}

data: {"type": "answer", "content": "高光谱显著目标检测的主要方法包括..."}

data: {"type": "done"}
```

**响应事件类型**:

| 类型 | 说明 | 数据格式 |
|------|------|----------|
| sources | 文档来源列表 | `{"type": "sources", "content": ["来源 1", "来源 2"]}` |
| thinking | 思考过程片段 | `{"type": "thinking", "content": "思考内容"}` |
| answer | 答案片段 | `{"type": "answer", "content": "答案内容"}` |
| error | 错误信息 | `{"type": "error", "content": "错误描述"}` |
| done | 流式传输完成 | `{"type": "done"}` |

**使用示例** (JavaScript):

```javascript
const eventSource = new EventSource('/api/rag/query/stream', {
  headers: { 'Content-Type': 'application/json' }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch(data.type) {
    case 'sources':
      console.log('文档来源:', data.content);
      break;
    case 'thinking':
      console.log('思考过程:', data.content);
      break;
    case 'answer':
      console.log('答案:', data.content);
      break;
    case 'done':
      console.log('传输完成');
      eventSource.close();
      break;
  }
};
```

**注意事项**:
- 该接口返回的是 SSE 流，需要使用 EventSource 或类似技术接收
- 思考过程可能为空（取决于模型是否支持推理输出）
- 对话历史会自动保存（当 use_history=true 时）

---

#### 1.2 标准查询接口

**端点**: `POST /api/rag/query`

**描述**: 一次性返回完整的 RAG 查询结果（非流式）。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| question | string | 是 | - | 用户问题 |
| k | integer | 否 | 5 | 检索的文档数量 |
| use_history | boolean | 否 | true | 是否使用对话历史 |

**请求示例**:

```json
{
  "question": "高光谱显著目标检测的主要方法有哪些？",
  "k": 5,
  "use_history": true
}
```

**响应示例**:

```json
{
  "code": 200,
  "data": {
    "question": "高光谱显著目标检测的主要方法有哪些？",
    "answer": "高光谱显著目标检测的主要方法包括基于稀疏表示的方法、基于深度学习的方法...",
    "thinking": "首先需要分析高光谱图像的特点，然后考虑显著性检测的常见技术路线...",
    "sources": ["paper1.pdf", "paper2.pdf", "paper3.pdf"],
    "session_id": "default_session"
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| question | string | 用户问题 |
| answer | string | 完整答案 |
| thinking | string | 完整思考过程（可能为空） |
| sources | array | 参考文档来源列表 |
| session_id | string | 当前会话 ID |

**注意事项**:
- 该接口会等待完整答案生成后才返回，响应时间较长
- 适合不需要实时反馈的场景
- 对话历史会自动保存

---

### 2. 文档检索接口

#### 2.1 文档搜索接口

**端点**: `POST /api/rag/search`

**描述**: 直接返回与查询相关的文档片段，不进行答案生成。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索查询 |
| k | integer | 否 | 5 | 返回的文档数量 |

**请求示例**:

```json
{
  "query": "高光谱目标检测",
  "k": 5
}
```

**响应示例**:

```json
{
  "code": 200,
  "data": {
    "query": "高光谱目标检测",
    "results": [
      {
        "content": "高光谱目标检测是高光谱遥感图像处理的重要应用领域...",
        "metadata": {
          "source": "paper1.pdf",
          "page": 1,
          "chunk_id": "abc123"
        }
      },
      {
        "content": "基于稀疏表示的高光谱目标检测方法...",
        "metadata": {
          "source": "paper2.pdf",
          "page": 3,
          "chunk_id": "def456"
        }
      }
    ],
    "count": 2
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| query | string | 搜索查询 |
| results | array | 文档结果列表 |
| results[].content | string | 文档片段内容 |
| results[].metadata | object | 文档元数据 |
| count | integer | 返回的文档数量 |

**注意事项**:
- 该接口仅返回文档片段，不生成答案
- 适合用于文档检索和预览场景
- 返回的文档按相关性排序

---

### 3. 文档管理接口

#### 3.1 处理文档接口

**端点**: `POST /api/rag/documents/process`

**描述**: 处理所有文档并构建向量存储。如果向量存储已有数据，会跳过处理。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "成功处理 10 个文档",
  "data": {
    "document_count": 10
  }
}
```

**注意事项**:
- 如果向量存储已有文档，会跳过处理（避免重复构建）
- 首次调用会处理所有 PDF 文件并创建 Embedding
- 处理时间取决于文档数量，可能较长

---

#### 3.2 重建文档索引接口

**端点**: `POST /api/rag/documents/rebuild`

**描述**: 强制删除现有向量存储并重新构建索引。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "成功重建向量存储",
  "data": {
    "document_count": 10
  }
}
```

**注意事项**:
- ⚠️ **危险操作**：会删除现有的向量存储
- 适用于修复索引损坏或更新文档内容
- 处理时间较长，请谨慎使用
- 如果遇到 HNSW 索引错误，可使用此接口修复

---

### 4. 记忆管理接口

#### 4.1 清空对话记忆

**端点**: `POST /api/rag/memory/clear`

**描述**: 清空当前会话的对话历史记录。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "对话记忆已清空"
}
```

**注意事项**:
- 清空后无法恢复对话历史
- 不影响向量存储中的文档数据

---

#### 4.2 获取记忆统计信息

**端点**: `GET /api/rag/memory/stats`

**描述**: 获取当前会话的记忆统计信息。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "data": {
    "message_count": 10,
    "session_id": "default_session",
    "storage_type": "memory"
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| message_count | integer | 对话消息数量 |
| session_id | string | 会话 ID |
| storage_type | string | 存储类型（memory/redis） |

---

#### 4.3 获取对话历史记录

**端点**: `GET /api/rag/memory/history`

**描述**: 获取格式化的对话历史记录。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "data": {
    "history": "用户：高光谱显著目标检测的主要方法有哪些？\nAI: 高光谱显著目标检测的主要方法包括...\n\n用户：这些方法有什么优缺点？\nAI: 各种方法的优缺点如下...",
    "session_id": "default_session"
  }
}
```

**注意事项**:
- 返回的是格式化后的文本字符串
- 包含完整的对话历史

---

### 5. 系统管理接口

#### 5.1 获取系统状态

**端点**: `GET /api/rag/status`

**描述**: 获取 RAG 系统的完整状态信息。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "data": {
    "initialized": true,
    "session_id": "default_session",
    "ollama_url": "http://localhost:11434",
    "llm_model": "qwen3:8b",
    "embedding_model": "qwen3-embedding:0.6b",
    "vector_store": {
      "total_documents": 10,
      "collection_name": "papers_collection",
      "persist_directory": "/path/to/chroma_db"
    },
    "memory": {
      "message_count": 5,
      "session_id": "default_session",
      "storage_type": "memory"
    }
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| initialized | boolean | 系统是否已初始化 |
| session_id | string | 当前会话 ID |
| ollama_url | string | Ollama 服务地址 |
| llm_model | string | LLM 模型名称 |
| embedding_model | string | Embedding 模型名称 |
| vector_store | object | 向量存储统计信息 |
| memory | object | 记忆管理统计信息 |

---

#### 5.2 健康检查接口

**端点**: `GET /api/rag/health`

**描述**: 检查 RAG 系统是否正常运行。

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "data": {
    "status": "ok",
    "message": "RAG 系统运行正常",
    "session_id": "default_session"
  }
}
```

**错误响应**:

```json
{
  "code": 500,
  "data": {
    "status": "error",
    "message": "RAG 系统初始化失败：Ollama 服务不可用"
  }
}
```

**注意事项**:
- 该接口会触发 RAG 系统初始化（如果尚未初始化）
- 适合用于服务监控和启动检查

---

## 使用示例

### 1. 使用 curl 调用

#### 流式查询

```bash
curl -X POST http://localhost:5000/api/rag/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "高光谱显著目标检测的主要方法有哪些？",
    "k": 5,
    "use_history": true
  }'
```

#### 标准查询

```bash
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "高光谱显著目标检测的主要方法有哪些？"
  }'
```

#### 文档搜索

```bash
curl -X POST http://localhost:5000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "高光谱目标检测",
    "k": 5
  }'
```

#### 获取系统状态

```bash
curl http://localhost:5000/api/rag/status
```

#### 健康检查

```bash
curl http://localhost:5000/api/rag/health
```

### 2. 使用 Python 调用

```python
import requests

# 标准查询
response = requests.post(
    'http://localhost:5000/api/rag/query',
    json={
        'question': '高光谱显著目标检测的主要方法有哪些？',
        'k': 5,
        'use_history': True
    }
)

result = response.json()
print(result['data']['answer'])

# 流式查询
import requests
import json

response = requests.post(
    'http://localhost:5000/api/rag/query/stream',
    json={'question': '高光谱显著目标检测的主要方法有哪些？'},
    stream=True
)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data = json.loads(line_str[6:])
            if data['type'] == 'answer':
                print(data['content'], end='', flush=True)
```

### 3. 使用 JavaScript 调用

```javascript
// 标准查询
async function query(question) {
  const response = await fetch('/api/rag/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, k: 5, use_history: true })
  });
  
  const result = await response.json();
  return result.data;
}

// 流式查询
async function queryStream(question) {
  const response = await fetch('/api/rag/query/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'answer') {
          console.log(data.content);
        }
      }
    }
  }
}
```

---

## 常见问题

### Q1: 遇到 "HNSW 索引错误" 怎么办？

**A**: 调用重建文档索引接口：

```bash
curl -X POST http://localhost:5000/api/rag/documents/rebuild
```

### Q2: 如何清空对话历史？

**A**: 调用清空记忆接口：

```bash
curl -X POST http://localhost:5000/api/rag/memory/clear
```

### Q3: 系统启动后需要手动初始化吗？

**A**: 不需要。RAG 系统采用按需初始化策略，第一次调用任意 API 时会自动初始化。

### Q4: 如何查看当前系统状态？

**A**: 调用系统状态接口：

```bash
curl http://localhost:5000/api/rag/status
```

### Q5: 流式输出如何在前端展示？

**A**: 使用 EventSource 或 Fetch API 的流式读取，参考上面的 JavaScript 示例。

---

## 注意事项

1. **Ollama 服务**: 确保 Ollama 服务正在运行（`http://localhost:11434`）
2. **文档目录**: PDF 文档应放置在 `data/papers` 目录下
3. **向量存储**: ChromaDB 数据存储在 `chroma_db` 目录
4. **会话隔离**: 当前版本使用单例模式，所有用户共享同一会话
5. **性能考虑**: 首次查询会触发系统初始化，响应时间较长
6. **错误处理**: 所有接口都有统一的错误处理机制，返回标准错误格式

---

## 版本信息

- **API 版本**: 1.0
- **最后更新**: 2026-03-01
- **技术栈**: Flask + LangChain + ChromaDB + Ollama

---

## 联系与支持

如有问题或建议，请联系开发团队。
