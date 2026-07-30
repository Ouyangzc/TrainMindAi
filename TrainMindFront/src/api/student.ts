import request from '@/utils/request'
import { getToken } from '@/utils/auth'
import type {
  StudentCourseListResult,
  StudentCourseResult,
  StudentQaMessageListResult,
  StudentQaMessageResult,
  StudentQaStreamEvent,
  StudentQaStreamEventName,
  StudentQaStreamHandlers,
  StudentQaSessionListResult,
  StudentQaSessionResult,
  StudentCourseOutlineResult,
  StudentDocumentListResult,
  StudentDocumentQuery,
  StudentPublishedDocumentResult,
  StudentLearningActivityListResult,
  StudentLearningActivityType
} from '@/types'

export function listMyCourses(): Promise<StudentCourseListResult> {
  return request({
    url: '/student/courses',
    method: 'get'
  })
}

export function getMyCourse(courseId: number): Promise<StudentCourseResult> {
  return request({
    url: `/student/courses/${courseId}`,
    method: 'get'
  })
}

export function listQaSessions(courseId: number): Promise<StudentQaSessionListResult> {
  return request({
    url: `/student/courses/${courseId}/chat/sessions`,
    method: 'get'
  })
}

export function createQaSession(courseId: number): Promise<StudentQaSessionResult> {
  return request({
    url: `/student/courses/${courseId}/chat/sessions`,
    method: 'post'
  })
}

export function deleteQaSession(courseId: number, sessionId: number) {
  return request({
    url: `/student/courses/${courseId}/chat/sessions/${sessionId}`,
    method: 'delete'
  })
}

export function listQaMessages(courseId: number, sessionId: number): Promise<StudentQaMessageListResult> {
  return request({
    url: `/student/courses/${courseId}/chat/sessions/${sessionId}`,
    method: 'get'
  })
}

export function askCourseQuestion(
  courseId: number,
  sessionId: number,
  question: string
): Promise<StudentQaMessageResult> {
  return request({
    url: `/student/courses/${courseId}/chat/sessions/${sessionId}/messages`,
    method: 'post',
    data: { question },
    timeout: 35000,
    headers: { repeatSubmit: false, interval: 1000 }
  })
}

export async function streamCourseQuestion(
  courseId: number,
  sessionId: number,
  question: string,
  handlers: StudentQaStreamHandlers = {}
) {
  const token = getToken()
  const response = await fetch(
    `${import.meta.env.VITE_APP_BASE_API}/student/courses/${courseId}/chat/sessions/${sessionId}/messages/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ question }),
      signal: handlers.signal
    }
  )
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  if (!response.body) throw new Error('流式响应不可用')

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    buffer = consumeSseBuffer(buffer, handlers)
  }

  buffer += decoder.decode()
  consumeSseBuffer(buffer, handlers, true)
}

function consumeSseBuffer(
  buffer: string,
  handlers: StudentQaStreamHandlers,
  flush = false
) {
  const frames = buffer.split(/\r?\n\r?\n/)
  const remaining = flush ? '' : frames.pop() || ''
  for (const frame of frames) {
    const event = parseSseFrame(frame)
    if (event) handlers.onEvent?.(event)
  }
  return remaining
}

function parseSseFrame(frame: string): StudentQaStreamEvent | null {
  let eventName: StudentQaStreamEventName = 'metadata'
  const dataLines: string[] = []
  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith('event:')) eventName = line.slice(6).trim() as StudentQaStreamEventName
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }
  if (!dataLines.length) return null
  return {
    event: eventName,
    data: JSON.parse(dataLines.join('\n'))
  }
}

export function getStudentCourseOutline(courseId: number): Promise<StudentCourseOutlineResult> {
  return request({
    url: `/student/courses/${courseId}/outline`,
    method: 'get'
  })
}

export function listStudentDocuments(
  courseId: number,
  query: StudentDocumentQuery
): Promise<StudentDocumentListResult> {
  return request({
    url: `/student/courses/${courseId}/documents`,
    method: 'get',
    params: query
  })
}

export function getStudentDocument(
  courseId: number,
  documentId: number
): Promise<StudentPublishedDocumentResult> {
  return request({
    url: `/student/courses/${courseId}/documents/${documentId}`,
    method: 'get'
  })
}

export function previewStudentDocument(courseId: number, documentId: number): Promise<Blob> {
  return request({
    url: `/student/courses/${courseId}/documents/${documentId}/preview`,
    method: 'get',
    responseType: 'blob',
    timeout: 30000
  })
}

export function downloadStudentDocument(courseId: number, documentId: number): Promise<Blob> {
  return request({
    url: `/student/courses/${courseId}/documents/${documentId}/download`,
    method: 'get',
    responseType: 'blob',
    timeout: 30000
  })
}

export function listStudentActivities(courseId: number): Promise<StudentLearningActivityListResult> {
  return request({
    url: `/student/courses/${courseId}/activities`,
    method: 'get'
  })
}

export function recordStudentActivity(
  courseId: number,
  activityType: Exclude<StudentLearningActivityType, 'chat'>,
  targetId?: number
) {
  return request({
    url: `/student/courses/${courseId}/activities`,
    method: 'post',
    data: { activityType, targetId },
    headers: { repeatSubmit: false }
  })
}
