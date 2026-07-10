export type CourseStatus = 'active' | 'archived'
export type ModuleStatus = 'active' | 'disabled'
export type DocumentStatus = 'active' | 'archived'
export type VersionStatus = 'uploaded' | 'parsing' | 'parsed' | 'failed'
export type MemberRole = 'owner' | 'teacher' | 'student'
export type MemberStatus = 'active' | 'disabled'

export interface CourseItem {
  id: number
  code: string
  name: string
  category: string
  ownerName: string
  status: CourseStatus
  moduleCount: number
  documentCount: number
  parsedCount: number
  studentCount: number
  currentVersion: string
  currentVersionStatus: string
  startDate: string
  updateTime: string
  remark: string
}

export interface CourseModuleItem {
  id: number
  courseId: number
  moduleCode: string
  moduleName: string
  sortOrder: number
  status: ModuleStatus
  documentCount: number
  remark: string
}

export interface CourseDocumentItem {
  id: number
  courseId: number
  moduleId: number | null
  title: string
  documentType: string
  originalFilename: string
  latestVersionNo: number
  documentStatus: DocumentStatus
  versionStatus: VersionStatus
  fileSize: string
  uploader: string
  updateTime: string
  parseErrorMessage?: string
}

export interface CourseMemberItem {
  id: number
  courseId: number
  userName: string
  nickName: string
  role: MemberRole
  status: MemberStatus
  validUntil: string
}

export const courseStatusOptions = [
  { label: '启用', value: 'active', type: 'success' },
  { label: '归档', value: 'archived', type: 'info' }
]

export const moduleStatusOptions = [
  { label: '启用', value: 'active', type: 'success' },
  { label: '停用', value: 'disabled', type: 'info' }
]

export const documentStatusOptions = [
  { label: '正常', value: 'active', type: 'success' },
  { label: '归档', value: 'archived', type: 'info' }
]

export const versionStatusOptions = [
  { label: '待解析', value: 'uploaded', type: 'info' },
  { label: '解析中', value: 'parsing', type: 'warning' },
  { label: '已解析', value: 'parsed', type: 'success' },
  { label: '解析失败', value: 'failed', type: 'danger' }
]

export const memberRoleOptions = [
  { label: '负责人', value: 'owner', type: 'danger' },
  { label: '讲师', value: 'teacher', type: 'warning' },
  { label: '学员', value: 'student', type: 'info' }
]

export const courses: CourseItem[] = [
  {
    id: 1001,
    code: 'AMT-737',
    name: '航空维修培训 - B737 基础',
    category: '航空维修培训',
    ownerName: '欧阳志成',
    status: 'active',
    moduleCount: 8,
    documentCount: 36,
    parsedCount: 28,
    studentCount: 126,
    currentVersion: 'KB-V3',
    currentVersionStatus: '已发布',
    startDate: '2026-07-01',
    updateTime: '2026-07-10 08:30:00',
    remark: '按 M1-M8 组织课件和公共资料'
  },
  {
    id: 1002,
    code: 'AMT-A320',
    name: '航空维修培训 - A320 机型差异',
    category: '航空维修培训',
    ownerName: '李明',
    status: 'active',
    moduleCount: 6,
    documentCount: 24,
    parsedCount: 19,
    studentCount: 84,
    currentVersion: 'KB-V1',
    currentVersionStatus: '已发布',
    startDate: '2026-07-05',
    updateTime: '2026-07-09 16:20:00',
    remark: '面向复训和差异化培训'
  },
  {
    id: 1003,
    code: 'SAFETY-001',
    name: '维修安全与人为因素',
    category: '通用安全课程',
    ownerName: '王蕾',
    status: 'archived',
    moduleCount: 4,
    documentCount: 13,
    parsedCount: 13,
    studentCount: 52,
    currentVersion: 'KB-V2',
    currentVersionStatus: '已发布',
    startDate: '2026-06-18',
    updateTime: '2026-07-02 11:05:00',
    remark: '历史班级保留查看'
  }
]

export const modules: CourseModuleItem[] = [
  { id: 0, courseId: 1001, moduleCode: 'PUBLIC', moduleName: '课程公共资料', sortOrder: 0, status: 'active', documentCount: 4, remark: '课程介绍、考核要求和通用参考资料' },
  { id: 11, courseId: 1001, moduleCode: 'M1', moduleName: '数学基础', sortOrder: 1, status: 'active', documentCount: 5, remark: '基础计算、单位换算' },
  { id: 12, courseId: 1001, moduleCode: 'M2', moduleName: '物理基础', sortOrder: 2, status: 'active', documentCount: 4, remark: '力学、热学、电学基础' },
  { id: 13, courseId: 1001, moduleCode: 'M3', moduleName: '电工基础', sortOrder: 3, status: 'active', documentCount: 6, remark: '电路、测量、接地' },
  { id: 14, courseId: 1001, moduleCode: 'M4', moduleName: '电子基础', sortOrder: 4, status: 'active', documentCount: 5, remark: '半导体和数字电路' },
  { id: 15, courseId: 1001, moduleCode: 'M5', moduleName: '数字技术', sortOrder: 5, status: 'active', documentCount: 4, remark: '航电计算机基础' },
  { id: 16, courseId: 1001, moduleCode: 'M6', moduleName: '材料与硬件', sortOrder: 6, status: 'active', documentCount: 3, remark: '材料识别和标准件' },
  { id: 17, courseId: 1001, moduleCode: 'M7', moduleName: '维修实践', sortOrder: 7, status: 'active', documentCount: 7, remark: '维护流程和工卡' },
  { id: 18, courseId: 1001, moduleCode: 'M8', moduleName: '空气动力学', sortOrder: 8, status: 'disabled', documentCount: 2, remark: '等待新版课件补齐' }
]

export const documents: CourseDocumentItem[] = [
  { id: 501, courseId: 1001, moduleId: null, title: '课程大纲与考核说明', documentType: 'pdf', originalFilename: 'B737-课程大纲.pdf', latestVersionNo: 2, documentStatus: 'active', versionStatus: 'parsed', fileSize: '2.4 MB', uploader: '欧阳志成', updateTime: '2026-07-10 08:18:00' },
  { id: 502, courseId: 1001, moduleId: null, title: '维修安全红线清单', documentType: 'docx', originalFilename: '维修安全红线清单.docx', latestVersionNo: 1, documentStatus: 'active', versionStatus: 'parsed', fileSize: '486 KB', uploader: '王蕾', updateTime: '2026-07-09 18:35:00' },
  { id: 511, courseId: 1001, moduleId: 11, title: 'M1-单位换算与工程数学', documentType: 'pptx', originalFilename: 'M1-单位换算与工程数学.pptx', latestVersionNo: 3, documentStatus: 'active', versionStatus: 'parsed', fileSize: '18.7 MB', uploader: '李明', updateTime: '2026-07-10 07:40:00' },
  { id: 512, courseId: 1001, moduleId: 11, title: 'M1-练习题汇总', documentType: 'xlsx', originalFilename: 'M1-练习题汇总.xlsx', latestVersionNo: 1, documentStatus: 'active', versionStatus: 'uploaded', fileSize: '732 KB', uploader: '李明', updateTime: '2026-07-10 08:05:00' },
  { id: 521, courseId: 1001, moduleId: 12, title: 'M2-力学基础课件', documentType: 'pptx', originalFilename: 'M2-力学基础课件.pptx', latestVersionNo: 2, documentStatus: 'active', versionStatus: 'parsing', fileSize: '22.1 MB', uploader: '赵强', updateTime: '2026-07-10 08:26:00' },
  { id: 531, courseId: 1001, moduleId: 13, title: 'M3-电路测量实训', documentType: 'docx', originalFilename: 'M3-电路测量实训.docx', latestVersionNo: 1, documentStatus: 'active', versionStatus: 'failed', fileSize: '1.1 MB', uploader: '赵强', updateTime: '2026-07-09 15:10:00', parseErrorMessage: '文档内容为空或无法提取文本' },
  { id: 571, courseId: 1001, moduleId: 17, title: 'M7-航线维护工卡示例', documentType: 'pdf', originalFilename: 'M7-航线维护工卡示例.pdf', latestVersionNo: 4, documentStatus: 'active', versionStatus: 'parsed', fileSize: '9.6 MB', uploader: '欧阳志成', updateTime: '2026-07-08 20:12:00' }
]

export const members: CourseMemberItem[] = [
  { id: 1, courseId: 1001, userName: 'oyang', nickName: '欧阳志成', role: 'owner', status: 'active', validUntil: '长期' },
  { id: 2, courseId: 1001, userName: 'liming', nickName: '李明', role: 'teacher', status: 'active', validUntil: '2026-12-31' },
  { id: 3, courseId: 1001, userName: 'wanglei', nickName: '王蕾', role: 'teacher', status: 'active', validUntil: '2026-12-31' },
  { id: 4, courseId: 1001, userName: 'student001', nickName: '张晨', role: 'student', status: 'active', validUntil: '2026-08-31' },
  { id: 5, courseId: 1001, userName: 'student002', nickName: '刘洋', role: 'student', status: 'disabled', validUntil: '2026-08-31' }
]

export function optionLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find(item => item.value === value)?.label || value
}

export function optionTagType(options: Array<{ type: string; value: string }>, value: string) {
  return options.find(item => item.value === value)?.type || 'info'
}
