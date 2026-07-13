import type { AjaxResult, BaseEntity, PageDomain, TableDataInfo } from './common'

export type CourseStatus = 'draft' | 'active' | 'disabled' | 'archived'
export type ModuleStatus = 'active' | 'disabled'
export type DocumentStatus = 'active' | 'archived'
export type VersionStatus = 'uploaded' | 'parsing' | 'parsed' | 'failed' | 'archived'

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

export type CourseListResult = TableDataInfo<Course[]>
export type CourseResult = AjaxResult<Course>
export type CourseModuleListResult = AjaxResult<CourseModule[]>
export type CourseDocumentListResult = AjaxResult<CourseDocument[]>
export type CourseDocumentVersionListResult = AjaxResult<CourseDocumentVersion[]>
