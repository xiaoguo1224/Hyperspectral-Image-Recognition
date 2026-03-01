<template>
  <div class="rag-layout">
    <div class="sidebar">
      <div class="brand">
        <div class="logo-box">
          <el-icon :size="22" color="#fff">
            <Cpu/>
          </el-icon>
        </div>
        <h2>RAG 知识引擎</h2>
      </div>

      <el-card class="status-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span><el-icon><Monitor/></el-icon> 系统状态</span>
            <span :class="['status-dot', status.initialized ? 'is-active' : 'is-error']"></span>
          </div>
        </template>
        <div class="status-item">
          <label>驱动模型</label>
          <span class="value-text">{{ status.llm_model || '加载中...' }}</span>
        </div>
        <div class="status-item">
          <label>向量模型</label>
          <span class="value-text">{{ status.embedding_model || '加载中...' }}</span>
        </div>
        <div class="status-item">
          <label>知识库容量</label>
          <el-tag size="small" effect="light" round type="primary">
            {{ status.total_documents || 0 }} 篇
          </el-tag>
        </div>
      </el-card>

      <div class="settings-area">
        <div class="section-title">检索设置</div>
        <div class="setting-item">
          <span class="label">上下文召回数 (K)</span>
          <el-input-number v-model="settings.k" :min="1" :max="10" size="small" controls-position="right"/>
        </div>
        <div class="setting-item">
          <span class="label">关联历史记忆</span>
          <el-switch v-model="settings.use_history" inline-prompt active-text="开" inactive-text="关"/>
        </div>
      </div>

      <div class="action-buttons">
        <el-button type="primary" plain icon="RefreshRight" @click="processDocs" :loading="isProcessing">
          增量处理文档
        </el-button>
        <el-button type="warning" plain icon="MagicStick" @click="rebuildDocs" :loading="isRebuilding">
          重建向量索引
        </el-button>
        <el-button type="danger" plain icon="Delete" @click="clearMemory">
          清空对话记忆
        </el-button>
      </div>
    </div>

    <div class="main-chat">
      <div class="chat-header">
        <div class="title-area">
          <h3>智能检索问答</h3>
          <span class="subtitle">基于检索增强生成，提供精准、可溯源的专业解答</span>
        </div>
        <div class="session-info" v-if="status.session_id">
          <el-icon>
            <Connection/>
          </el-icon>
          {{ status.session_id }}
        </div>
      </div>

      <div
          class="message-list"
          ref="messageListRef"
          v-loading="isHistoryLoading"
          element-loading-text="正在同步记忆..."
          element-loading-background="rgba(247, 249, 252, 0.8)"
      >
        <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message-wrapper', msg.role === 'user' ? 'is-user' : 'is-ai']"
        >
          <div class="avatar">
            <el-icon :size="20">
              <User v-if="msg.role === 'user'"/>
              <Platform v-else/>
            </el-icon>
          </div>

          <div class="message-content">
            <div v-if="msg.role === 'ai' && (msg.thinking || msg.isThinking)" class="thinking-box">
              <div class="thinking-header" @click="msg.showThinking = !msg.showThinking">
                <div class="th-left">
                  <el-icon :class="{'is-rotating': msg.isThinking && !msg.showThinking}">
                    <component :is="msg.showThinking ? 'CaretBottom' : 'CaretRight'"/>
                  </el-icon>
                  <span class="th-title">
                    {{ msg.isThinking ? '深度思考中...' : '思考过程' }}
                  </span>
                </div>
                <span class="th-time" v-if="!msg.isThinking">{{ msg.thinkingTime || '' }}</span>
              </div>
              <el-collapse-transition>
                <div v-show="msg.showThinking" class="thinking-body">
                  <div class="markdown-body thinking-text"
                       v-html="renderMarkdown(msg.thinking) || '正在加载检索策略...'"></div>
                  <span v-if="msg.isThinking" class="cursor-blink">▍</span>
                </div>
              </el-collapse-transition>
            </div>

            <div class="text-bubble" v-if="msg.content || (msg.role === 'user')">
              <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <span v-if="msg.role === 'ai' && !msg.isThinking && msg.isGenerating" class="cursor-blink">▍</span>
            </div>

            <div v-if="msg.sources && msg.sources.length > 0" class="sources-box">
              <div class="source-title">
                <el-icon>
                  <Document/>
                </el-icon>
                参考文档：
              </div>
              <div class="source-tags">
                <el-tooltip v-for="(source, idx) in msg.sources" :key="idx" :content="source" placement="top">
                  <el-tag size="small" type="info" class="source-tag">
                    {{ source.length > 15 ? source.substring(0, 15) + '...' : source }}
                  </el-tag>
                </el-tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-wrapper">
          <el-input
              v-model="inputMsg"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              placeholder="发送消息，探讨知识库内容... (Shift + Enter 换行)"
              resize="none"
              class="custom-input"
              :disabled="isHistoryLoading"
              @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button
              type="primary"
              class="send-btn"
              circle
              :icon="Position"
              :disabled="!inputMsg.trim() || isGenerating || isHistoryLoading"
              @click="sendMessage"
          />
        </div>
        <div class="input-footer">
          <span>AI 生成的内容仅供参考，请结合实际文档核实。</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, nextTick} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  Cpu, Monitor, User, Platform, Document, Position,
  RefreshRight, Delete, CaretBottom, CaretRight, MagicStick, Connection
} from '@element-plus/icons-vue'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code>' +
            hljs.highlight(str, {language: lang, ignoreIllegals: true}).value +
            '</code></pre>';
      } catch (__) {
      }
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
  }
})

const BASE_URL = import.meta.env.VITE_RAG_API || 'http://localhost:5001/api/rag'

const inputMsg = ref('')
const isGenerating = ref(false)
const isProcessing = ref(false)
const isRebuilding = ref(false)
const isHistoryLoading = ref(true) // 新增：记录是否正在加载历史记录
const messageListRef = ref(null)

const status = ref({
  initialized: false,
  llm_model: '',
  embedding_model: '',
  total_documents: 0,
  session_id: ''
})

const settings = ref({
  k: 5,
  use_history: true
})

// 默认的欢迎消息
const defaultWelcomeMessage = {
  role: 'ai',
  content: '您好！我是专属知识引擎助手。\n\n我已经准备好回答关于知识库的问题了。你可以问我：\n* **概念解析**\n* **原理解释**\n* **文档摘要**',
  thinking: '',
  isThinking: false,
  isGenerating: false,
  showThinking: false,
  sources: []
};

// 初始置空，等待加载完成再决定放入历史记录还是欢迎语
const messages = ref([])

const renderMarkdown = (text) => {
  if (!text) return ''
  return md.render(text)
}

const scrollToBottom = async () => {
  await nextTick()

  if (messageListRef.value) {
    messageListRef.value.scrollTo({
      top: messageListRef.value.scrollHeight,
      behavior: 'auto'
    })
  }

  const thinkingBodies = document.querySelectorAll('.thinking-body');
  if (thinkingBodies.length > 0) {
    const lastThinkingBody = thinkingBodies[thinkingBodies.length - 1];
    if (lastThinkingBody.scrollHeight > lastThinkingBody.clientHeight) {
      lastThinkingBody.scrollTop = lastThinkingBody.scrollHeight;
    }
  }
}

// 获取历史记录逻辑
const loadHistory = async () => {
  isHistoryLoading.value = true; // 开始加载
  try {
    const res = await fetch(`${BASE_URL}/memory/history?format_type=json`);
    const {code, data} = await res.json();

    if (code === 200 && data && data.history) {
      const historyData = data.history;

      if (historyData === '暂无对话历史' || historyData === '暂无对话记录') {
        messages.value = [defaultWelcomeMessage]; // 后端无记录，展示欢迎语
        return;
      }

      let parsedMessages = [];
      let parsedJson = null;

      try {
        if (typeof historyData === 'string' && (historyData.startsWith('[') || historyData.startsWith('{'))) {
          parsedJson = JSON.parse(historyData);
        } else if (Array.isArray(historyData)) {
          parsedJson = historyData;
        }
      } catch (e) {
      }

      if (parsedJson && Array.isArray(parsedJson)) {
        parsedMessages = parsedJson
            .filter(item => {
              const type = item.type || (item.id && item.id[item.id.length - 1]);
              return type === 'human' || type === 'ai' || type === 'HumanMessage' || type === 'AIMessage';
            })
            .map(item => {
              const type = item.type || (item.id && item.id[item.id.length - 1]);
              return {
                role: (type === 'human' || type === 'HumanMessage') ? 'user' : 'ai',
                content: item.content || item.data?.content || '',
                thinking: '', isThinking: false, isGenerating: false, showThinking: false, sources: []
              };
            });
      } else if (typeof historyData === 'string') {
        const regex = /(?:^|\n)(?:\d+\.\s*)?(用户：|用户:|\[用户\]|AI：|AI:|\[AI\])/;
        const tokens = historyData.split(regex);
        let currentRole = null;
        let currentContent = '';

        for (let i = 0; i < tokens.length; i++) {
          const token = tokens[i];
          if (!token) continue;

          if (/^(用户：|用户:|\[用户\])$/.test(token)) {
            if (currentRole && currentContent.trim()) {
              parsedMessages.push({
                role: currentRole,
                content: currentContent.trim(),
                thinking: '',
                isThinking: false,
                isGenerating: false,
                showThinking: false,
                sources: []
              });
            }
            currentRole = 'user';
            currentContent = '';
          } else if (/^(AI：|AI:|\[AI\])$/.test(token)) {
            if (currentRole && currentContent.trim()) {
              parsedMessages.push({
                role: currentRole,
                content: currentContent.trim(),
                thinking: '',
                isThinking: false,
                isGenerating: false,
                showThinking: false,
                sources: []
              });
            }
            currentRole = 'ai';
            currentContent = '';
          } else {
            if (currentRole) {
              currentContent += token;
            }
          }
        }
        if (currentRole && currentContent.trim()) {
          parsedMessages.push({
            role: currentRole,
            content: currentContent.trim(),
            thinking: '',
            isThinking: false,
            isGenerating: false,
            showThinking: false,
            sources: []
          });
        }
      }

      // 根据解析结果赋值
      if (parsedMessages.length > 0) {
        messages.value = parsedMessages;
      } else {
        messages.value = [defaultWelcomeMessage];
      }
    } else {
      messages.value = [defaultWelcomeMessage];
    }
  } catch (error) {
    console.warn('未获取到历史记录或解析失败，使用默认欢迎语。', error);
    messages.value = [defaultWelcomeMessage];
  } finally {
    // 无论成功与否，结束加载状态并滚动到底部
    isHistoryLoading.value = false;
    setTimeout(() => {
      scrollToBottom();
    }, 100);
  }
};

const fetchStatus = async () => {
  try {
    const res = await fetch(`${BASE_URL}/status`)
    const {code, data} = await res.json()
    if (code === 200) {
      status.value = {
        initialized: data.initialized,
        llm_model: data.llm_model,
        embedding_model: data.embedding_model,
        total_documents: data.vector_store?.total_documents || 0,
        session_id: data.session_id
      }
    }
  } catch (error) {
    console.error('状态获取失败', error)
  }
}

const sendMessage = async () => {
  if (!inputMsg.value.trim() || isGenerating.value) return

  const question = inputMsg.value
  inputMsg.value = ''

  messages.value.push({role: 'user', content: question})
  scrollToBottom()

  const aiMsgIndex = messages.value.length
  messages.value.push({
    role: 'ai',
    content: '',
    thinking: '',
    isThinking: true,
    isGenerating: true,
    showThinking: true,
    sources: []
  })

  isGenerating.value = true
  let startTime = Date.now()

  try {
    const response = await fetch(`${BASE_URL}/query/stream`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        question: question,
        k: settings.value.k,
        use_history: settings.value.use_history
      })
    })

    if (!response.ok) throw new Error('网络请求错误')

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const {done, value} = await reader.read()
      if (done) break

      buffer += decoder.decode(value, {stream: true})
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const dataStr = line.slice(6).trim()
            if (!dataStr) continue

            const data = JSON.parse(dataStr)
            const currentMsg = messages.value[aiMsgIndex]

            if (data.type === 'thinking') {
              currentMsg.thinking += data.content
            } else if (data.type === 'answer') {
              if (currentMsg.isThinking) {
                currentMsg.isThinking = false
                currentMsg.showThinking = false
                currentMsg.thinkingTime = ((Date.now() - startTime) / 1000).toFixed(1) + 's'
              }
              currentMsg.content += data.content
            } else if (data.type === 'sources') {
              currentMsg.sources = data.content
            } else if (data.type === 'error') {
              currentMsg.content += `\n\n[系统异常]: ${data.content}`
            } else if (data.type === 'done') {
              currentMsg.isThinking = false
              currentMsg.isGenerating = false
              isGenerating.value = false
            }
            scrollToBottom()
          } catch (e) {
            console.warn('解析流数据片段失败:', e)
          }
        }
      }
    }
  } catch (error) {
    messages.value[aiMsgIndex].content += '\n\n[连接异常]：抱歉，服务出现异常。'
    messages.value[aiMsgIndex].isThinking = false
    messages.value[aiMsgIndex].isGenerating = false
  } finally {
    isGenerating.value = false
    scrollToBottom()
  }
}

const processDocs = async () => {
  isProcessing.value = true
  try {
    const res = await fetch(`${BASE_URL}/documents/process`, {method: 'POST'})
    const {code, data, message} = await res.json()
    if (code === 200) {
      ElMessage.success(message || '文档处理成功')
      fetchStatus()
    } else {
      ElMessage.warning(message || '处理遇到问题')
    }
  } catch (error) {
    ElMessage.error('服务异常')
  } finally {
    isProcessing.value = false
  }
}

const rebuildDocs = async () => {
  try {
    await ElMessageBox.confirm('重建索引将清空现有向量数据库并重新解析所有文件，耗时可能较长，确认执行？', '危险操作', {
      type: 'warning',
      confirmButtonText: '强制重建',
      confirmButtonClass: 'el-button--danger'
    })

    isRebuilding.value = true
    const res = await fetch(`${BASE_URL}/documents/rebuild`, {method: 'POST'})
    const {code, message} = await res.json()
    if (code === 200) {
      ElMessage.success(message || '索引重建成功')
      fetchStatus()
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('重建失败')
  } finally {
    isRebuilding.value = false
  }
}

const clearMemory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空当前的对话记忆吗？AI 将忘记之前的上下文。', '清空记忆', {type: 'info'})
    const res = await fetch(`${BASE_URL}/memory/clear`, {method: 'POST'})
    if (res.ok) {
      ElMessage.success('记忆已清空')
      messages.value = [defaultWelcomeMessage] // 清空后恢复欢迎语
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchStatus()
  loadHistory() // 调用加载历史的逻辑
})
</script>

<style scoped>
/* 全局布局 */
.rag-layout {
  display: flex;
  height: 85vh;
  width: 85vw;
  background-color: #f7f9fc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  overflow: hidden;
}

/* ---------------- 侧边栏 ---------------- */
.sidebar {
  width: 280px;
  background-color: #ffffff;
  border-right: 1px solid #eef0f4;
  display: flex;
  flex-direction: column;
  padding: 24px 20px;
  box-sizing: border-box;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo-box {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #409EFF, #3a8ee6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.3);
}

.brand h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1d1e23;
  letter-spacing: 0.5px;
}

.status-card {
  border-radius: 12px;
  border: 1px solid #ebeef5;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.is-active {
  background-color: #67c23a;
  box-shadow: 0 0 6px rgba(103, 194, 58, 0.6);
}

.status-dot.is-error {
  background-color: #f56c6c;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  font-size: 13px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-item label {
  color: #8c92a4;
}

.status-item .value-text {
  color: #303133;
  font-weight: 500;
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-area {
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 24px;
  border: 1px solid #eef0f4;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #8c92a4;
  margin-bottom: 16px;
  text-transform: uppercase;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-item .label {
  font-size: 13px;
  color: #303133;
}

.action-buttons {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-buttons .el-button {
  margin-left: 0;
  border-radius: 8px;
  justify-content: flex-start;
  padding-left: 20px;
}

/* ---------------- 主聊天区 ---------------- */
.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f7f9fc;
  position: relative;
}

.chat-header {
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #eef0f4;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 5;
}

.title-area h3 {
  margin: 0 0 6px 0;
  color: #1d1e23;
  font-size: 18px;
}

.title-area .subtitle {
  font-size: 12px;
  color: #8c92a4;
}

.session-info {
  font-size: 12px;
  color: #a0a5b3;
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f0f2f5;
  padding: 4px 10px;
  border-radius: 12px;
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 5%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 100%;
}

.message-wrapper.is-user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409EFF, #3a8ee6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.2);
  margin-top: 4px;
}

.is-ai .avatar {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.2);
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 85%;
}

.is-user .message-content {
  align-items: flex-end;
}

/* 思考过程区块 */
.thinking-box {
  background-color: #f3f4f6;
  border-left: 3px solid #9ca3af;
  border-radius: 0 8px 8px 0;
  padding: 0;
  overflow: hidden;
  transition: all 0.3s;
}

.thinking-header {
  padding: 10px 14px;
  font-size: 13px;
  color: #4b5563;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  user-select: none;
}

.thinking-header:hover {
  background-color: #e5e7eb;
}

.th-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.th-time {
  font-size: 12px;
  color: #9ca3af;
}

.is-rotating {
  animation: pulse-op 1.5s infinite;
}

@keyframes pulse-op {
  0% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.5;
  }
}

.thinking-body {
  padding: 0 14px 14px 14px;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.6;

  max-height: 250px;
  overflow-y: auto;
}

.thinking-body::-webkit-scrollbar {
  width: 5px;
}

.thinking-body::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.thinking-body::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.thinking-body::-webkit-scrollbar-track {
  background: transparent;
}


/* 气泡正文 */
.text-bubble {
  position: relative;
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 12px;
  border-top-left-radius: 2px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02);
  border: 1px solid #f0f2f5;
  overflow-x: auto;
}

.is-user .text-bubble {
  background: #409EFF;
  border: none;
  border-radius: 12px;
  border-top-right-radius: 2px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.is-user .markdown-body {
  color: #ffffff;
}

.is-user .markdown-body :deep(p) {
  margin: 0;
}

/* 光标闪烁 */
.cursor-blink {
  display: inline-block;
  width: 8px;
  height: 16px;
  background-color: #1f2937;
  vertical-align: middle;
  margin-left: 2px;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

/* 来源区块 */
.sources-box {
  margin-top: 4px;
  padding: 10px 14px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px dashed #dcdfe6;
}

.source-title {
  font-size: 12px;
  color: #8c92a4;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-tag {
  cursor: default;
}

/* 底部输入区 */
.input-area {
  padding: 20px 15%;
  background: linear-gradient(0deg, #f7f9fc 80%, rgba(247, 249, 252, 0) 100%);
  position: relative;
  z-index: 10;
}

.input-wrapper {
  position: relative;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02);
  border: 1px solid #eef0f4;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: #409EFF;
  box-shadow: 0 6px 24px rgba(64, 158, 255, 0.1);
}

.custom-input :deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  background: transparent;
  padding: 16px 60px 16px 20px;
  font-size: 15px;
  line-height: 1.6;
  color: #1f2937;
}

.send-btn {
  position: absolute;
  right: 12px;
  bottom: 12px;
  transition: all 0.2s;
}

.input-footer {
  margin-top: 12px;
  text-align: center;
  font-size: 12px;
  color: #a0a5b3;
}

/* ========================================================= */
/* Markdown 核心样式适配                   */
/* ========================================================= */

.markdown-body {
  font-size: 15px;
  line-height: 1.6;
  color: #2c3e50;
  word-wrap: break-word;
}

.is-user .markdown-body {
  color: #ffffff;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(h1) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body :deep(h2) {
  font-size: 1.3em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body :deep(h3) {
  font-size: 1.1em;
}

.markdown-body :deep(p) {
  margin-top: 0;
  margin-bottom: 0.8em;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-top: 0;
  margin-bottom: 0.8em;
  padding-left: 2em;
}

.markdown-body :deep(li) {
  margin-bottom: 0.25em;
}

.markdown-body :deep(blockquote) {
  margin: 0.8em 0;
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  background-color: #f8f9fa;
  border-radius: 2px;
}

.markdown-body :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 4px;
  font-family: Consolas, Monaco, monospace;
}

.is-user .markdown-body :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
}

.markdown-body :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 8px;
  margin-top: 0;
  margin-bottom: 0.8em;
}

.markdown-body :deep(pre code) {
  display: inline;
  max-width: auto;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
}

.markdown-body :deep(table) {
  display: block;
  width: 100%;
  overflow: auto;
  margin-top: 0;
  margin-bottom: 1em;
  border-spacing: 0;
  border-collapse: collapse;
}

.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body :deep(table tr) {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body :deep(table tr:nth-child(2n)) {
  background-color: #f6f8fa;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.thinking-text.markdown-body {
  color: #6b7280;
  font-size: 14px;
}
</style>