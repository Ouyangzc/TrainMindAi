<template>
  <section class="assistant-page">
    <div class="page-heading">
      <div>
        <span class="kicker">COURSE AI</span>
        <h1>AI 学习助教</h1>
        <p>回答仅依据当前课程已发布资料，并保留引用来源。</p>
      </div>
      <el-button :icon="Plus" plain @click="startNewConversation">新对话</el-button>
    </div>

    <div class="assistant-layout">
      <aside class="sessions-panel">
        <div class="panel-title">
          <strong>历史对话</strong>
          <el-button link :icon="Refresh" :loading="sessionsLoading" @click="loadSessions" />
        </div>
        <div v-if="sessionsLoading && !sessions.length" class="session-skeleton">
          <el-skeleton :rows="4" animated />
        </div>
        <el-empty v-else-if="!sessions.length" :image-size="58" description="还没有历史对话" />
        <button
          v-for="session in sessions"
          v-else
          :key="session.id"
          type="button"
          class="session-item"
          :class="{ 'session-item--active': session.id === activeSessionId }"
          @click="selectSession(session.id)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span>
            <strong>{{ session.title }}</strong>
            <small>{{ formatSessionTime(session.updateTime || session.createTime) }}</small>
          </span>
        </button>
      </aside>

      <div class="chat-panel">
        <header class="chat-header">
          <div>
            <strong>{{ activeSessionTitle }}</strong>
            <span><i></i> 当前课程知识库已连接</span>
          </div>
        </header>

        <div ref="messageScroller" v-loading="messagesLoading" class="message-list">
          <div v-if="!messagesLoading && !messages.length" class="welcome-card">
            <div class="ai-mark">AI</div>
            <h2>从一个课程问题开始</h2>
            <p>我会检索当前课程的发布资料。找不到足够依据时，我会明确告诉你，而不是编造答案。</p>
            <div class="suggestions">
              <button v-for="item in suggestions" :key="item" type="button" @click="useSuggestion(item)">
                {{ item }}
              </button>
            </div>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="message"
            :class="`message--${message.role}`"
          >
            <div v-if="message.role === 'assistant'" class="message-avatar">AI</div>
            <div class="message-content">
              <div class="message-bubble" :class="`message-bubble--${message.status}`">
                <div v-if="message.status === 'insufficient_evidence'" class="status-label">
                  <el-icon><Warning /></el-icon> 当前资料依据不足
                </div>
                <div v-else-if="message.status === 'service_unavailable'" class="status-label status-label--error">
                  <el-icon><CircleClose /></el-icon> 问答服务暂时不可用
                </div>
                <p>{{ message.content }}</p>
                <el-button
                  v-if="message.status === 'service_unavailable'"
                  type="danger"
                  link
                  :disabled="sending"
                  @click="retryMessage(message)"
                >
                  重新提问
                </el-button>
              </div>

              <div v-if="message.role === 'assistant' && message.citations?.length" class="citations">
                <div class="citations-title">回答依据</div>
                <button
                  v-for="citation in message.citations"
                  :key="citation.id"
                  type="button"
                  class="citation-card"
                  @click="openCitation(citation)"
                >
                  <span class="citation-rank">{{ citation.rankNo || 1 }}</span>
                  <span class="citation-main">
                    <strong>{{ citation.documentTitle }}</strong>
                    <small>{{ citationLocation(citation) }}</small>
                  </span>
                  <el-icon><ArrowRight /></el-icon>
                </button>
              </div>
            </div>
          </article>

          <article v-if="sending" class="message message--assistant">
            <div class="message-avatar">AI</div>
            <div class="thinking"><i></i><i></i><i></i><span>正在检索课程资料</span></div>
          </article>
        </div>

        <footer class="composer">
          <el-input
            v-model="question"
            type="textarea"
            resize="none"
            :rows="2"
            maxlength="2000"
            placeholder="输入与当前课程相关的问题，按 Ctrl + Enter 发送"
            :disabled="sending"
            @keydown.ctrl.enter.prevent="sendQuestion()"
          />
          <div class="composer-actions">
            <span>AI 回答仅供学习参考，请以课程原始资料为准。</span>
            <el-button type="primary" :icon="Promotion" :loading="sending" @click="sendQuestion()">
              发送
            </el-button>
          </div>
        </footer>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowRight, ChatLineRound, CircleClose, Plus, Promotion, Refresh, Warning
} from '@element-plus/icons-vue'
import {
  askCourseQuestion, createQaSession, listQaMessages, listQaSessions
} from '@/api/student'
import type { StudentQaCitation, StudentQaMessage, StudentQaSession } from '@/types'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => Number(route.params.courseId))
const sessionsLoading = ref(false)
const messagesLoading = ref(false)
const sending = ref(false)
const sessions = ref<StudentQaSession[]>([])
const messages = ref<StudentQaMessage[]>([])
const activeSessionId = ref<number>()
const question = ref('')
const messageScroller = ref<HTMLElement>()
let loadSequence = 0

const suggestions = [
  '这门课程主要包含哪些学习内容？',
  '请解释课程中的核心概念',
  '有哪些容易忽略的操作要求？'
]
const activeSessionTitle = computed(() => sessions.value.find(
  (item: StudentQaSession) => item.id === activeSessionId.value
)?.title || '新对话')

async function loadSessions() {
  const sequence = ++loadSequence
  sessionsLoading.value = true
  try {
    const response = await listQaSessions(courseId.value)
    if (sequence !== loadSequence) return
    sessions.value = response.data || []
  } catch {
    if (sequence === loadSequence) ElMessage.error('历史对话加载失败')
  } finally {
    if (sequence === loadSequence) sessionsLoading.value = false
  }
}

async function selectSession(sessionId: number) {
  if (sending.value) return
  const sequence = ++loadSequence
  activeSessionId.value = sessionId
  messagesLoading.value = true
  messages.value = []
  try {
    const response = await listQaMessages(courseId.value, sessionId)
    if (sequence !== loadSequence) return
    messages.value = response.data || []
    scrollToBottom()
  } catch {
    if (sequence === loadSequence) ElMessage.error('对话消息加载失败')
  } finally {
    if (sequence === loadSequence) messagesLoading.value = false
  }
}

function startNewConversation() {
  if (sending.value) return
  loadSequence++
  activeSessionId.value = undefined
  messages.value = []
  question.value = ''
}

async function ensureSession() {
  if (activeSessionId.value) return activeSessionId.value
  const response = await createQaSession(courseId.value)
  if (!response.data) throw new Error('会话创建失败')
  activeSessionId.value = response.data.id
  sessions.value.unshift(response.data)
  return response.data.id
}

async function sendQuestion(value = question.value) {
  const normalized = value.trim()
  if (!normalized || sending.value) return
  sending.value = true
  question.value = ''
  try {
    const sessionId = await ensureSession()
    const optimisticMessage: StudentQaMessage = {
      id: -Date.now(), sessionId, courseId: courseId.value, knowledgeBaseVersionId: 0,
      role: 'user', content: normalized, status: 'completed', citations: []
    }
    messages.value.push(optimisticMessage)
    scrollToBottom()
    const response = await askCourseQuestion(courseId.value, sessionId, normalized)
    if (response.data) messages.value.push(response.data)
    await loadSessions()
    scrollToBottom()
  } catch {
    question.value = normalized
    ElMessage.error('问题发送失败，内容已保留，请重试')
  } finally {
    sending.value = false
  }
}

function retryMessage(message: StudentQaMessage) {
  const index = messages.value.findIndex((item: StudentQaMessage) => item.id === message.id)
  const previousQuestion = [...messages.value.slice(0, index)].reverse().find(
    (item: StudentQaMessage) => item.role === 'user'
  )
  if (previousQuestion) sendQuestion(previousQuestion.content)
}

function useSuggestion(value: string) {
  question.value = value
}

function openCitation(citation: StudentQaCitation) {
  router.push({
    path: `/student/courses/${courseId.value}/library`,
    query: {
      documentId: citation.documentId.toString(),
      page: citation.pageStart?.toString()
    }
  })
}

function citationLocation(citation: StudentQaCitation) {
  const locations = []
  if (citation.sectionTitle) locations.push(citation.sectionTitle)
  if (citation.pageStart) locations.push(`第 ${citation.pageStart} 页`)
  if (!locations.length && citation.versionNo) locations.push(`资料 V${citation.versionNo}`)
  return locations.join(' · ') || '查看引用资料'
}

function formatSessionTime(value?: string) {
  if (!value) return ''
  return value.slice(5, 16)
}

function scrollToBottom() {
  nextTick(() => {
    if (messageScroller.value) messageScroller.value.scrollTop = messageScroller.value.scrollHeight
  })
}

watch(() => route.params.courseId, () => {
  loadSequence++
  sessions.value = []
  messages.value = []
  activeSessionId.value = undefined
  loadSessions()
}, { immediate: true })
</script>

<style scoped lang="scss">
.assistant-page { max-width: 1240px; margin: 0 auto; }
.page-heading { margin-bottom: 20px; display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }
.kicker { color: #3978a8; font-size: 11px; font-weight: 700; letter-spacing: 0.14em; }
.page-heading h1 { margin: 7px 0 5px; font-size: 26px; }
.page-heading p { margin: 0; color: #748194; font-size: 14px; }
.assistant-layout { min-height: 640px; display: grid; grid-template-columns: 220px minmax(0, 1fr); overflow: hidden; border: 1px solid #e1e7ef; border-radius: 18px; background: #fff; box-shadow: 0 10px 34px rgba(30, 57, 84, 0.06); }
.sessions-panel { padding: 17px 12px; background: #f7f9fc; border-right: 1px solid #e6ebf1; }
.panel-title { padding: 0 7px 12px; display: flex; align-items: center; justify-content: space-between; }
.session-skeleton { padding: 8px; }
.session-item { width: 100%; margin: 3px 0; padding: 11px 10px; display: flex; align-items: flex-start; gap: 9px; text-align: left; color: #5b687a; border: 0; border-radius: 10px; background: transparent; cursor: pointer; }
.session-item:hover, .session-item--active { color: #225e91; background: #e9f2fb; }
.session-item > span { min-width: 0; flex: 1; }
.session-item strong, .session-item small { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.session-item strong { color: inherit; font-size: 13px; font-weight: 600; }
.session-item small { margin-top: 5px; color: #9aa4b2; font-size: 11px; }
.chat-panel { min-width: 0; display: grid; grid-template-rows: auto minmax(380px, 1fr) auto; }
.chat-header { padding: 16px 21px; border-bottom: 1px solid #e9edf2; }
.chat-header > div { display: flex; align-items: center; justify-content: space-between; gap: 15px; }
.chat-header span { display: flex; align-items: center; gap: 7px; color: #29826f; font-size: 12px; }
.chat-header i { width: 7px; height: 7px; border-radius: 50%; background: #29b78f; }
.message-list { max-height: 570px; padding: 23px; overflow-y: auto; background: #fbfcfe; }
.welcome-card { max-width: 650px; margin: 55px auto 0; padding: 26px; text-align: center; border: 1px solid #e4e9f0; border-radius: 16px; background: linear-gradient(135deg, #f2f8fb, #f7f4ff); }
.ai-mark, .message-avatar { display: grid; place-items: center; color: #fff; background: linear-gradient(135deg, #275f9a, #6d5bd0); font-size: 11px; font-weight: 700; }
.ai-mark { width: 38px; height: 38px; margin: 0 auto 12px; border-radius: 12px; }
.welcome-card h2 { margin: 0 0 8px; font-size: 20px; }
.welcome-card p { margin: 0; color: #68778a; font-size: 13px; line-height: 1.7; }
.suggestions { margin-top: 18px; display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
.suggestions button { padding: 8px 11px; color: #456178; border: 1px solid #d9e2eb; border-radius: 999px; background: #fff; cursor: pointer; }
.message { margin: 16px 0; display: flex; align-items: flex-start; gap: 10px; }
.message--user { justify-content: flex-end; }
.message-avatar { width: 30px; height: 30px; flex: 0 0 auto; border-radius: 9px; }
.message-content { max-width: min(78%, 720px); }
.message-bubble { padding: 12px 15px; color: #314258; border: 1px solid #e0e6ed; border-radius: 4px 14px 14px 14px; background: #fff; }
.message--user .message-bubble { color: #fff; border: 0; border-radius: 14px 14px 4px 14px; background: #1c4665; }
.message-bubble--insufficient_evidence { border-color: #ead6a7; background: #fffbf1; }
.message-bubble--service_unavailable { border-color: #efc2c2; background: #fff7f7; }
.message-bubble p { margin: 0; white-space: pre-wrap; line-height: 1.75; font-size: 14px; }
.status-label { margin-bottom: 7px; display: flex; align-items: center; gap: 5px; color: #9b6a13; font-size: 12px; font-weight: 600; }
.status-label--error { color: #bc4a50; }
.citations { margin-top: 9px; }
.citations-title { margin: 0 0 6px 3px; color: #8491a2; font-size: 11px; }
.citation-card { width: 100%; margin-top: 6px; padding: 10px 12px; display: flex; align-items: center; gap: 10px; text-align: left; color: #536478; border: 1px solid #dfe6ee; border-radius: 10px; background: #fff; cursor: pointer; }
.citation-card:hover { color: #356da0; border-color: #8bb6d9; }
.citation-rank { width: 22px; height: 22px; display: grid; place-items: center; color: #356a98; border-radius: 7px; background: #eaf3fb; font-size: 11px; }
.citation-main { min-width: 0; flex: 1; }
.citation-main strong, .citation-main small { display: block; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.citation-main strong { font-size: 12px; }
.citation-main small { margin-top: 3px; color: #8a96a6; font-size: 11px; }
.thinking { padding: 10px 13px; display: flex; align-items: center; gap: 5px; color: #798698; border: 1px solid #e0e6ed; border-radius: 4px 13px 13px; background: #fff; font-size: 12px; }
.thinking i { width: 5px; height: 5px; border-radius: 50%; background: #6884a0; animation: pulse 1.1s infinite; }
.thinking i:nth-child(2) { animation-delay: .15s; }.thinking i:nth-child(3) { animation-delay: .3s; }.thinking span { margin-left: 5px; }
.composer { padding: 14px 18px; border-top: 1px solid #e7ebf0; background: #fff; }
.composer-actions { margin-top: 9px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.composer-actions span { color: #98a1ae; font-size: 11px; }
@keyframes pulse { 0%, 70%, 100% { opacity: .25; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-2px); } }
@media (max-width: 900px) { .assistant-layout { grid-template-columns: 1fr; }.sessions-panel { display: none; }.message-content { max-width: 88%; } }
@media (max-width: 600px) { .page-heading { align-items: flex-start; }.page-heading p { display: none; }.assistant-layout { min-height: 560px; border-radius: 13px; }.message-list { padding: 15px; }.composer-actions span { display: none; } }
</style>
