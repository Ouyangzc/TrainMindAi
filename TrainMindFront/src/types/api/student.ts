import type { AjaxResult } from './common'

export type StudentCourseAvailability =
  | 'available'
  | 'content_preparing'
  | 'not_started'
  | 'expired'
  | 'access_disabled'
  | 'course_disabled'

export interface StudentCourse {
  courseId: number
  courseCode: string
  courseName: string
  courseCategory?: string
  description?: string
  ownerName?: string
  availability: StudentCourseAvailability
  accessStartAt?: string
  accessEndAt?: string
  knowledgeBaseId?: number
  publishedVersionId?: number
  publishedVersionNo?: number
  allowDownload: boolean
  lastVisitedAt?: string
}

export type StudentCourseListResult = AjaxResult<StudentCourse[]>
export type StudentCourseResult = AjaxResult<StudentCourse>

export type StudentQaMessageStatus =
  | 'pending'
  | 'grounded'
  | 'insufficient_evidence'
  | 'service_unavailable'
  | 'completed'

export interface StudentQaSession {
  id: number
  courseId: number
  title: string
  status: 'active'
  createTime?: string
  updateTime?: string
}

export interface StudentQaCitation {
  id: number
  messageId: number
  chunkId?: number
  documentId: number
  documentVersionId: number
  documentTitle: string
  versionNo?: number
  sourceFile?: string
  pageStart?: number
  pageEnd?: number
  sectionTitle?: string
  quote?: string
  score?: number
  rankNo?: number
}

export interface StudentQaMessage {
  id: number
  sessionId: number
  courseId: number
  knowledgeBaseVersionId: number
  role: 'user' | 'assistant'
  content: string
  status: StudentQaMessageStatus
  rejectReason?: string
  retrievalLogRef?: number
  citations: StudentQaCitation[]
  createTime?: string
  updateTime?: string
}

export type StudentQaSessionListResult = AjaxResult<StudentQaSession[]>
export type StudentQaSessionResult = AjaxResult<StudentQaSession>
export type StudentQaMessageListResult = AjaxResult<StudentQaMessage[]>
export type StudentQaMessageResult = AjaxResult<StudentQaMessage>

export interface StudentPublishedDocument {
  documentId: number
  documentVersionId: number
  title: string
  documentType?: string
  versionNo?: number
  originalFilename?: string
  fileExt?: string
  fileSize?: number
  moduleId?: number
  moduleCode?: string
  moduleName?: string
  moduleDescription?: string
  moduleSortOrder?: number
}

export interface StudentCourseModule {
  moduleId?: number
  moduleCode?: string
  moduleName: string
  description?: string
  sortOrder?: number
  documents: StudentPublishedDocument[]
}

export interface StudentCourseOutline {
  courseId: number
  knowledgeBaseVersionId: number
  versionNo: number
  modules: StudentCourseModule[]
}

export interface StudentDocumentQuery {
  moduleId?: number
  keyword?: string
  fileExt?: string
  pageNum: number
  pageSize: number
}

export type StudentCourseOutlineResult = AjaxResult<StudentCourseOutline>
export type StudentPublishedDocumentResult = AjaxResult<StudentPublishedDocument>

export interface StudentDocumentListResult {
  code: number
  msg: string
  total: number
  rows: StudentPublishedDocument[]
}

export type StudentLearningActivityType = 'course_view' | 'module_view' | 'document_view' | 'chat'

export interface StudentLearningActivity {
  id: number
  courseId: number
  activityType: StudentLearningActivityType
  targetId?: number
  targetTitle?: string
  targetDetail?: string
  occurredAt: string
}

export type StudentLearningActivityListResult = AjaxResult<StudentLearningActivity[]>
