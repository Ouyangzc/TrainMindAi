import request from '@/utils/request'
import type {
  StudentCourseListResult,
  StudentCourseResult,
  StudentQaMessageListResult,
  StudentQaMessageResult,
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
