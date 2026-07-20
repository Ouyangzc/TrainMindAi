import type { AjaxResult, BaseEntity, PageDomain, TableDataInfo } from './common'

export type CourseStatus = 'draft' | 'active' | 'disabled' | 'archived'
export type ModuleStatus = 'active' | 'disabled'
export type DocumentStatus = 'active' | 'archived'
export type VersionStatus = 'uploaded' | 'parsing' | 'parsed' | 'failed' | 'archived'
export type KnowledgeBaseVersionStatus = 'draft' | 'building' | 'ready' | 'published' | 'archived' | 'failed'
export type CourseAccessRole = 'owner' | 'teacher' | 'student'
export type CourseAccessStatus = 'active' | 'disabled'

export interface CourseQueryParams extends PageDomain {
  courseCode?: string
  courseName?: string
  courseCategory?: string
  status?: CourseStatus | ''
}

export interface Course extends BaseEntity {
  id?: number
  tenantId?: number
  courseCode?: string
  courseName?: string
  courseCategory?: string
  description?: string
  ownerUserId?: number
  ownerName?: string
  startDate?: string
  status?: CourseStatus
  sortOrder?: number
  delFlag?: string
  moduleCount?: number
  documentCount?: number
  parsedCount?: number
  studentCount?: number
  currentVersion?: string
  currentVersionStatus?: string
}

export interface CourseModule extends BaseEntity {
  id?: number
  tenantId?: number
  courseId?: number
  moduleCode?: string
  moduleName?: string
  description?: string
  sortOrder?: number
  status?: ModuleStatus
  delFlag?: string
  documentCount?: number
}

export interface CourseDocument extends BaseEntity {
  id?: number
  tenantId?: number
  courseId?: number
  moduleId?: number | null
  title?: string
  documentType?: string
  latestVersionId?: number
  status?: DocumentStatus
  delFlag?: string
  moduleName?: string
  versionNo?: number
  originalFilename?: string
  fileExt?: string
  fileSize?: number
  versionStatus?: VersionStatus
  parseErrorMessage?: string
}

export interface CourseDocumentVersion extends BaseEntity {
  id?: number
  tenantId?: number
  courseId?: number
  moduleId?: number | null
  documentId?: number
  versionNo?: number
  originalFilename?: string
  fileExt?: string
  contentType?: string
  fileSize?: number
  checksumMd5?: string
  bucket?: string
  objectName?: string
  status?: VersionStatus
  parseTaskId?: number
  parseErrorMessage?: string
}

export interface DocumentParseTask extends BaseEntity {
  id?: number
  documentId?: number
  documentVersionId?: number
  status?: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  currentStep?: string
  progress?: number
  errorCode?: string
  errorMessage?: string
  retryCount?: number
  startedAt?: string
  finishedAt?: string
}

export interface KnowledgeBase extends BaseEntity {
  id?: number
  tenantId?: number
  courseId?: number
  name?: string
  description?: string
  currentVersionId?: number
  status?: string
}

export interface KnowledgeBaseVersion extends BaseEntity {
  id?: number
  knowledgeBaseId?: number
  versionNo?: number
  status?: KnowledgeBaseVersionStatus
  chunkCount?: number
  buildTaskId?: number
  buildErrorMessage?: string
  publishedAt?: string
  publishedBy?: string
}

export interface KnowledgeBaseVersionDocument extends BaseEntity {
  id?: number
  knowledgeBaseVersionId?: number
  documentId?: number
  documentVersionId?: number
  documentTitle?: string
  versionNo?: number
  originalFilename?: string
  fileExt?: string
  versionStatus?: VersionStatus
  moduleId?: number | null
}

export interface KnowledgeBaseBuildTask extends BaseEntity {
  id?: number
  status?: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  currentStep?: string
  progress?: number
  errorMessage?: string
}

export interface CourseMember extends BaseEntity {
  id?: number
  courseId?: number
  userId?: number
  userName?: string
  nickName?: string
  accessRole?: CourseAccessRole
  accessStatus?: CourseAccessStatus
  startAt?: string
  endAt?: string
}

export type CourseListResult = TableDataInfo<Course[]>
export type CourseResult = AjaxResult<Course>
export type CourseModuleListResult = AjaxResult<CourseModule[]>
export type CourseDocumentListResult = AjaxResult<CourseDocument[]>
export type CourseDocumentVersionListResult = AjaxResult<CourseDocumentVersion[]>
export type DocumentParseTaskResult = AjaxResult<DocumentParseTask>
export type KnowledgeBaseResult = AjaxResult<KnowledgeBase>
export type KnowledgeBaseVersionResult = AjaxResult<KnowledgeBaseVersion>
export type KnowledgeBaseVersionListResult = AjaxResult<KnowledgeBaseVersion[]>
export type KnowledgeBaseSnapshotResult = AjaxResult<KnowledgeBaseVersionDocument[]>
export type KnowledgeBaseBuildTaskResult = AjaxResult<KnowledgeBaseBuildTask>
export type CourseMemberListResult = AjaxResult<CourseMember[]>
export type CourseMemberResult = AjaxResult<CourseMember>
