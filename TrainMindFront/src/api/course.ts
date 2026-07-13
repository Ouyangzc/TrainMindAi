import request from '@/utils/request'
import type {
  AjaxResult,
  Course,
  CourseDocumentListResult,
  CourseDocumentVersionListResult,
  CourseListResult,
  CourseModule,
  CourseModuleListResult,
  CourseQueryParams,
  CourseResult
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

export function listCourseDocument(courseId: number, query?: Record<string, unknown>): Promise<CourseDocumentListResult> {
  return request({
    url: `/course/${courseId}/documents`,
    method: 'get',
    params: query
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
