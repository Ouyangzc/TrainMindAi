import request from '@/utils/request'
import type {
  AjaxResult,
  Course,
  CourseDocumentListResult,
  CourseDocumentVersionListResult,
  CourseListResult,
  CourseModule,
  CourseModuleListResult,
  CourseMember,
  CourseMemberListResult,
  CourseMemberResult,
  CourseQueryParams,
  CourseResult,
  DocumentParseTaskResult,
  KnowledgeBaseBuildTaskResult,
  KnowledgeBaseResult,
  KnowledgeBaseSnapshotResult,
  KnowledgeBaseVersionListResult,
  KnowledgeBaseVersionResult
} from '@/types'

export function listCourse(query: CourseQueryParams): Promise<CourseListResult> {
  return request({
    url: '/course/list',
    method: 'get',
    params: query
  })
}

export function getCourse(courseId: number): Promise<CourseResult> {
  return request({
    url: `/course/${courseId}`,
    method: 'get'
  })
}

export function addCourse(data: Course): Promise<AjaxResult> {
  return request({
    url: '/course',
    method: 'post',
    data
  })
}

export function updateCourse(data: Course): Promise<AjaxResult> {
  return request({
    url: '/course',
    method: 'put',
    data
  })
}

export function delCourse(courseIds: number | number[]): Promise<AjaxResult> {
  return request({
    url: `/course/${courseIds}`,
    method: 'delete'
  })
}

export function listCourseModule(courseId: number, query?: CourseModule): Promise<CourseModuleListResult> {
  return request({
    url: `/course/${courseId}/modules`,
    method: 'get',
    params: query
  })
}

export function addCourseModule(courseId: number, data: CourseModule): Promise<AjaxResult> {
  return request({
    url: `/course/${courseId}/modules`,
    method: 'post',
    data: { ...data, courseId }
  })
}

export function updateCourseModule(courseId: number, moduleId: number, data: CourseModule): Promise<AjaxResult> {
  return request({
    url: `/course/${courseId}/modules/${moduleId}`,
    method: 'put',
    data: { ...data, id: moduleId, courseId }
  })
}

export function delCourseModule(courseId: number, moduleId: number): Promise<AjaxResult> {
  return request({
    url: `/course/${courseId}/modules/${moduleId}`,
    method: 'delete'
  })
}

export function listCourseDocument(courseId: number, query?: Record<string, unknown>): Promise<CourseDocumentListResult> {
  return request({
    url: `/course/${courseId}/documents`,
    method: 'get',
    params: query
  })
}

export function uploadCourseDocument(courseId: number, data: FormData): Promise<AjaxResult> {
  return request({
    url: `/course/${courseId}/documents/upload`,
    method: 'post',
    data
  })
}

export function uploadCourseDocumentVersion(
  courseId: number,
  documentId: number,
  data: FormData
): Promise<AjaxResult> {
  return request({
    url: `/course/${courseId}/documents/${documentId}/versions`,
    method: 'post',
    data
  })
}

export function listCourseDocumentVersion(
  courseId: number,
  documentId: number
): Promise<CourseDocumentVersionListResult> {
  return request({
    url: `/course/${courseId}/documents/${documentId}/versions`,
    method: 'get'
  })
}

export function downloadCourseDocumentVersion(
  courseId: number,
  documentId: number,
  versionId: number
): Promise<Blob> {
  return request({
    url: `/course/${courseId}/documents/${documentId}/versions/${versionId}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

export function parseCourseDocumentVersion(
  courseId: number,
  documentId: number,
  versionId: number
): Promise<DocumentParseTaskResult> {
  return request({
    url: `/course/${courseId}/documents/${documentId}/versions/${versionId}/parse`,
    method: 'post'
  })
}

export function getCourseDocumentParseTask(
  courseId: number,
  documentId: number,
  versionId: number
): Promise<DocumentParseTaskResult> {
  return request({
    url: `/course/${courseId}/documents/${documentId}/versions/${versionId}/parse-task`,
    method: 'get'
  })
}

export function delCourseDocument(courseId: number, documentId: number): Promise<AjaxResult> {
  return request({
    url: `/course/${courseId}/documents/${documentId}`,
    method: 'delete'
  })
}

export function getKnowledgeBase(courseId: number): Promise<KnowledgeBaseResult> {
  return request({ url: `/course/${courseId}/knowledge-base`, method: 'get' })
}

export function listKnowledgeBaseVersion(courseId: number): Promise<KnowledgeBaseVersionListResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions`, method: 'get' })
}

export function createKnowledgeBaseDraft(courseId: number): Promise<KnowledgeBaseVersionResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions`, method: 'post' })
}

export function getKnowledgeBaseSnapshot(
  courseId: number,
  versionId: number
): Promise<KnowledgeBaseSnapshotResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions/${versionId}/documents`, method: 'get' })
}

export function saveKnowledgeBaseSnapshot(
  courseId: number,
  versionId: number,
  documentVersionIds: number[]
): Promise<KnowledgeBaseSnapshotResult> {
  return request({
    url: `/course/${courseId}/knowledge-base/versions/${versionId}/documents`,
    method: 'put',
    data: { documentVersionIds }
  })
}

export function buildKnowledgeBaseVersion(
  courseId: number,
  versionId: number
): Promise<KnowledgeBaseBuildTaskResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions/${versionId}/build`, method: 'post' })
}

export function getKnowledgeBaseBuildStatus(
  courseId: number,
  versionId: number
): Promise<KnowledgeBaseBuildTaskResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions/${versionId}/build-status`, method: 'get' })
}

export function publishKnowledgeBaseVersion(
  courseId: number,
  versionId: number
): Promise<KnowledgeBaseVersionResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions/${versionId}/publish`, method: 'post' })
}

export function rollbackKnowledgeBaseVersion(
  courseId: number,
  versionId: number
): Promise<KnowledgeBaseVersionResult> {
  return request({ url: `/course/${courseId}/knowledge-base/versions/${versionId}/rollback`, method: 'post' })
}

export function listCourseMember(courseId: number): Promise<CourseMemberListResult> {
  return request({ url: `/course/${courseId}/members`, method: 'get' })
}

export function addCourseMember(courseId: number, data: CourseMember): Promise<CourseMemberResult> {
  return request({ url: `/course/${courseId}/members`, method: 'post', data })
}

export function updateCourseMember(
  courseId: number,
  memberId: number,
  data: CourseMember
): Promise<CourseMemberResult> {
  return request({ url: `/course/${courseId}/members/${memberId}`, method: 'put', data })
}

export function delCourseMember(courseId: number, memberId: number): Promise<AjaxResult> {
  return request({ url: `/course/${courseId}/members/${memberId}`, method: 'delete' })
}

export function transferCourseOwner(courseId: number, targetUserId: number): Promise<CourseMemberResult> {
  return request({ url: `/course/${courseId}/owner/transfer`, method: 'put', data: { targetUserId } })
}
