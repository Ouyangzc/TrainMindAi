<template>
  <div class="app-container course-detail">
    <div class="detail-header">
      <div>
        <div class="breadcrumb-line">
          <el-button link icon="ArrowLeft" @click="goBack">课程管理</el-button>
          <span>/</span>
          <span>{{ course?.code }}</span>
        </div>
        <h2>{{ course?.name }}</h2>
        <div class="header-meta">
          <el-tag :type="optionTagType(courseStatusOptions, course?.status || '')">
            {{ optionLabel(courseStatusOptions, course?.status || '') }}
          </el-tag>
          <span>负责人：{{ course?.ownerName }}</span>
          <span>分类：{{ course?.category }}</span>
          <span>更新时间：{{ course?.updateTime }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button icon="Edit" @click="handleMockAction('编辑课程')">编辑</el-button>
        <el-button type="primary" icon="Upload" @click="activeTab = 'documents'">上传资料</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="course-tabs">
      <el-tab-pane label="基本信息" name="basic">
        <div class="basic-grid">
          <div class="info-panel">
            <div class="panel-title">课程信息</div>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="课程编码">{{ course?.code }}</el-descriptions-item>
              <el-descriptions-item label="课程分类">{{ course?.category }}</el-descriptions-item>
              <el-descriptions-item label="主负责人">{{ course?.ownerName }}</el-descriptions-item>
              <el-descriptions-item label="开课日期">{{ course?.startDate }}</el-descriptions-item>
              <el-descriptions-item label="课程状态">
                <el-tag :type="optionTagType(courseStatusOptions, course?.status || '')">
                  {{ optionLabel(courseStatusOptions, course?.status || '') }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="当前知识库">{{ course?.currentVersion }} / {{ course?.currentVersionStatus }}</el-descriptions-item>
              <el-descriptions-item label="备注" :span="2">{{ course?.remark }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="metric-panel">
            <div class="metric-item">
              <span>模块数</span>
              <strong>{{ courseModules.length }}</strong>
            </div>
            <div class="metric-item">
              <span>资料数</span>
              <strong>{{ courseDocuments.length }}</strong>
            </div>
            <div class="metric-item">
              <span>已解析</span>
              <strong>{{ parsedDocumentCount }}</strong>
            </div>
            <div class="metric-item">
              <span>成员数</span>
              <strong>{{ courseMembers.length }}</strong>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="模块管理" name="modules">
        <div class="tab-toolbar">
          <el-button type="primary" plain icon="Plus" @click="handleMockAction('新增模块')">新增模块</el-button>
          <el-button icon="Sort" @click="handleMockAction('保存排序')">保存排序</el-button>
        </div>
        <el-table :data="courseModules" row-key="id">
          <el-table-column label="排序" prop="sortOrder" width="90" align="center" />
          <el-table-column label="模块编码" prop="moduleCode" width="120" />
          <el-table-column label="模块名称" prop="moduleName" min-width="180" />
          <el-table-column label="资料数" prop="documentCount" width="90" align="center" />
          <el-table-column label="状态" prop="status" width="90" align="center">
            <template #default="scope">
              <el-tag :type="optionTagType(moduleStatusOptions, scope.row.status)">
                {{ optionLabel(moduleStatusOptions, scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="备注" prop="remark" min-width="220" :show-overflow-tooltip="true" />
          <el-table-column label="操作" width="210" align="center" class-name="small-padding fixed-width">
            <template #default>
              <el-button link type="primary" icon="Edit" @click="handleMockAction('编辑模块')">编辑</el-button>
              <el-button link type="primary" icon="Switch" @click="handleMockAction('启停模块')">启停</el-button>
              <el-button link type="primary" icon="Delete" @click="handleMockAction('删除模块')">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="资料管理" name="documents">
        <div class="document-layout">
          <aside class="module-tree">
            <div class="tree-title">资料范围</div>
            <el-menu :default-active="selectedModuleKey" @select="selectedModuleKey = $event">
              <el-menu-item index="all">
                <el-icon><Folder /></el-icon>
                <span>全部资料</span>
              </el-menu-item>
              <el-menu-item index="public">
                <el-icon><Collection /></el-icon>
                <span>课程公共资料</span>
              </el-menu-item>
              <el-menu-item
                v-for="item in normalModules"
                :key="item.id"
                :index="String(item.id)"
              >
                <el-icon><Document /></el-icon>
                <span>{{ item.moduleCode }} {{ item.moduleName }}</span>
              </el-menu-item>
            </el-menu>
          </aside>

          <section class="document-main">
            <el-form :model="documentQuery" :inline="true" class="document-search">
              <el-form-item label="关键词">
                <el-input v-model="documentQuery.keyword" placeholder="资料名称或文件名" clearable style="width: 220px" />
              </el-form-item>
              <el-form-item label="文件类型">
                <el-select v-model="documentQuery.documentType" placeholder="全部" clearable style="width: 140px">
                  <el-option label="PDF" value="pdf" />
                  <el-option label="DOCX" value="docx" />
                  <el-option label="PPTX" value="pptx" />
                  <el-option label="XLSX" value="xlsx" />
                </el-select>
              </el-form-item>
              <el-form-item label="解析状态">
                <el-select v-model="documentQuery.versionStatus" placeholder="全部" clearable style="width: 150px">
                  <el-option
                    v-for="item in versionStatusOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" icon="Search">搜索</el-button>
                <el-button icon="Refresh" @click="resetDocumentQuery">重置</el-button>
              </el-form-item>
            </el-form>

            <div class="tab-toolbar compact">
              <el-button type="primary" plain icon="Upload" @click="openUploadDialog('new')">上传资料</el-button>
              <el-button icon="Download" @click="handleMockAction('批量下载')">批量下载</el-button>
            </div>

            <el-table :data="filteredDocuments">
              <el-table-column label="资料名称" min-width="220" :show-overflow-tooltip="true">
                <template #default="scope">
                  <div class="document-title">
                    <el-tag size="small" effect="plain">{{ scope.row.documentType.toUpperCase() }}</el-tag>
                    <span>{{ scope.row.title }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="所属模块" width="150">
                <template #default="scope">{{ moduleName(scope.row.moduleId) }}</template>
              </el-table-column>
              <el-table-column label="版本" width="80" align="center">
                <template #default="scope">V{{ scope.row.latestVersionNo }}</template>
              </el-table-column>
              <el-table-column label="解析状态" width="110" align="center">
                <template #default="scope">
                  <el-tooltip
                    v-if="scope.row.versionStatus === 'failed'"
                    :content="scope.row.parseErrorMessage"
                    placement="top"
                  >
                    <el-tag :type="optionTagType(versionStatusOptions, scope.row.versionStatus)">
                      {{ optionLabel(versionStatusOptions, scope.row.versionStatus) }}
                    </el-tag>
                  </el-tooltip>
                  <el-tag v-else :type="optionTagType(versionStatusOptions, scope.row.versionStatus)">
                    {{ optionLabel(versionStatusOptions, scope.row.versionStatus) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="大小" prop="fileSize" width="100" />
              <el-table-column label="上传人" prop="uploader" width="110" />
              <el-table-column label="更新时间" prop="updateTime" width="170" />
              <el-table-column label="操作" width="330" align="center" class-name="small-padding fixed-width">
                <template #default="scope">
                  <el-button link type="primary" icon="Upload" @click="openUploadDialog('version')">新版本</el-button>
                  <el-button link type="primary" icon="Clock" @click="openVersionDialog(scope.row)">版本历史</el-button>
                  <el-button link type="primary" icon="Download" @click="handleMockAction('下载原文件')">下载</el-button>
                  <el-button link type="primary" icon="Cpu" @click="handleMockAction('手动解析')">解析</el-button>
                  <el-button link type="primary" icon="Delete" @click="handleMockAction('删除资料')">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="知识库治理" name="knowledge">
        <div class="knowledge-shell">
          <div class="knowledge-status">
            <div>
              <span class="muted">知识库名称</span>
              <strong>{{ course?.name }}知识库</strong>
            </div>
            <div>
              <span class="muted">当前发布版本</span>
              <strong>{{ course?.currentVersion }}</strong>
            </div>
            <div>
              <span class="muted">活动版本状态</span>
              <el-tag type="success">{{ course?.currentVersionStatus }}</el-tag>
            </div>
            <el-button type="primary" disabled>创建草稿</el-button>
          </div>
          <el-tabs model-value="draft">
            <el-tab-pane label="草稿资料" name="draft">
              <el-empty description="知识库治理后端确认后接入" />
            </el-tab-pane>
            <el-tab-pane label="构建任务" name="tasks">
              <el-empty description="等待构建任务接口" />
            </el-tab-pane>
            <el-tab-pane label="版本历史" name="versions">
              <el-empty description="等待版本历史接口" />
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-tab-pane>

      <el-tab-pane label="课程成员" name="members">
        <div class="tab-toolbar">
          <el-button type="primary" plain icon="Plus" @click="handleMockAction('添加成员')">添加成员</el-button>
          <el-button icon="Connection" @click="handleMockAction('转移负责人')">转移负责人</el-button>
        </div>
        <el-table :data="courseMembers">
          <el-table-column label="用户名" prop="userName" width="140" />
          <el-table-column label="姓名" prop="nickName" width="140" />
          <el-table-column label="角色" prop="role" width="100" align="center">
            <template #default="scope">
              <el-tag :type="optionTagType(memberRoleOptions, scope.row.role)">
                {{ optionLabel(memberRoleOptions, scope.row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="status" width="100" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
                {{ scope.row.status === 'active' ? '有效' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="有效期至" prop="validUntil" width="160" />
          <el-table-column label="操作" width="220" align="center" class-name="small-padding fixed-width">
            <template #default>
              <el-button link type="primary" icon="Edit" @click="handleMockAction('编辑成员')">编辑</el-button>
              <el-button link type="primary" icon="Switch" @click="handleMockAction('启停成员')">启停</el-button>
              <el-button link type="primary" icon="Delete" @click="handleMockAction('移除成员')">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog :title="uploadTitle" v-model="uploadOpen" width="560px" append-to-body>
      <el-form label-width="96px">
        <el-form-item label="所属模块">
          <el-select v-model="uploadForm.moduleId" placeholder="请选择模块" style="width: 100%">
            <el-option label="课程公共资料" :value="0" />
            <el-option
              v-for="item in normalModules"
              :key="item.id"
              :label="`${item.moduleCode} ${item.moduleName}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资料标题">
          <el-input v-model="uploadForm.title" placeholder="请输入资料标题" />
        </el-form-item>
        <el-form-item label="上传文件">
          <el-upload drag action="#" :auto-upload="false" :limit="1">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖入文件或点击选择</div>
            <template #tip>
              <div class="el-upload__tip">支持 pdf、docx、pptx、xlsx，单文件最大 200MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" v-model="uploadForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitUpload">确 定</el-button>
          <el-button @click="uploadOpen = false">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog title="版本历史" v-model="versionOpen" width="720px" append-to-body>
      <el-table :data="versionRows">
        <el-table-column label="版本" prop="versionNo" width="80" align="center" />
        <el-table-column label="文件名" prop="filename" min-width="220" />
        <el-table-column label="状态" prop="status" width="110" align="center">
          <template #default="scope">
            <el-tag :type="optionTagType(versionStatusOptions, scope.row.status)">
              {{ optionLabel(versionStatusOptions, scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" prop="fileSize" width="100" />
        <el-table-column label="上传时间" prop="updateTime" width="170" />
        <el-table-column label="操作" width="90" align="center">
          <template #default>
            <el-button link type="primary" icon="Download" @click="handleMockAction('下载历史版本')">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="CourseDetail">
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { Collection, Document, Folder, UploadFilled } from '@element-plus/icons-vue'
import {
  courses,
  modules,
  documents,
  members,
  courseStatusOptions,
  moduleStatusOptions,
  versionStatusOptions,
  memberRoleOptions,
  optionLabel,
  optionTagType,
  type CourseDocumentItem,
  type VersionStatus
} from './mock'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => Number(route.params.courseId || 1001))
const course = computed(() => courses.find(item => item.id === courseId.value) || courses[0])
const activeTab = ref('basic')
const selectedModuleKey = ref('all')
const uploadOpen = ref(false)
const uploadTitle = ref('上传资料')
const versionOpen = ref(false)
const currentDocument = ref<CourseDocumentItem | null>(null)

const documentQuery = reactive({
  keyword: '',
  documentType: '',
  versionStatus: '' as VersionStatus | ''
})

const uploadForm = reactive({
  moduleId: 0,
  title: '',
  remark: ''
})

const courseModules = computed(() => modules.filter(item => item.courseId === course.value.id))
const normalModules = computed(() => courseModules.value.filter(item => item.id !== 0))
const courseDocuments = computed(() => documents.filter(item => item.courseId === course.value.id))
const courseMembers = computed(() => members.filter(item => item.courseId === course.value.id))
const parsedDocumentCount = computed(() => courseDocuments.value.filter(item => item.versionStatus === 'parsed').length)

const filteredDocuments = computed(() => {
  const keyword = documentQuery.keyword.trim().toLowerCase()
  return courseDocuments.value.filter(item => {
    const matchModule =
      selectedModuleKey.value === 'all' ||
      (selectedModuleKey.value === 'public' && item.moduleId === null) ||
      String(item.moduleId) === selectedModuleKey.value
    const matchKeyword =
      !keyword ||
      item.title.toLowerCase().includes(keyword) ||
      item.originalFilename.toLowerCase().includes(keyword)
    const matchType = !documentQuery.documentType || item.documentType === documentQuery.documentType
    const matchStatus = !documentQuery.versionStatus || item.versionStatus === documentQuery.versionStatus
    return matchModule && matchKeyword && matchType && matchStatus
  })
})

const versionRows = computed(() => {
  if (!currentDocument.value) {
    return []
  }
  return Array.from({ length: currentDocument.value.latestVersionNo }).map((_, index) => {
    const versionNo = currentDocument.value!.latestVersionNo - index
    return {
      versionNo: `V${versionNo}`,
      filename: currentDocument.value!.originalFilename,
      status: versionNo === currentDocument.value!.latestVersionNo ? currentDocument.value!.versionStatus : 'parsed',
      fileSize: currentDocument.value!.fileSize,
      updateTime: currentDocument.value!.updateTime
    }
  })
})

function moduleName(moduleId: number | null) {
  if (moduleId === null) {
    return '课程公共资料'
  }
  const item = courseModules.value.find(module => module.id === moduleId)
  return item ? `${item.moduleCode} ${item.moduleName}` : '-'
}

function resetDocumentQuery() {
  documentQuery.keyword = ''
  documentQuery.documentType = ''
  documentQuery.versionStatus = ''
}

function openUploadDialog(mode: 'new' | 'version') {
  uploadTitle.value = mode === 'new' ? '上传资料' : '上传新版本'
  uploadOpen.value = true
}

function submitUpload() {
  uploadOpen.value = false
  ElMessage.success(`${uploadTitle.value}：页面效果阶段，待确认后接入后端`)
}

function openVersionDialog(row: CourseDocumentItem) {
  currentDocument.value = row
  versionOpen.value = true
}

function handleMockAction(name: string) {
  ElMessage.info(`${name}：页面效果阶段，待确认后接入后端`)
}

function goBack() {
  router.push('/course')
}
</script>

<style scoped lang="scss">
.course-detail {
  .detail-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e6eb;
  }

  .breadcrumb-line {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #909399;
    font-size: 13px;
  }

  h2 {
    margin: 8px 0;
    color: #1f2d3d;
    font-size: 22px;
    font-weight: 600;
  }

  .header-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    color: #606266;
    font-size: 13px;
  }

  .header-actions {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }

  .course-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 14px;
    }
  }

  .basic-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 14px;
  }

  .info-panel,
  .metric-panel,
  .knowledge-shell {
    border: 1px solid #e5e6eb;
    border-radius: 6px;
    background: #fff;
  }

  .info-panel {
    padding: 14px;
  }

  .panel-title {
    margin-bottom: 12px;
    color: #1f2d3d;
    font-size: 15px;
    font-weight: 600;
  }

  .metric-panel {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0;
    overflow: hidden;
  }

  .metric-item {
    min-height: 96px;
    padding: 18px;
    border-right: 1px solid #ebeef5;
    border-bottom: 1px solid #ebeef5;
  }

  .metric-item span {
    display: block;
    margin-bottom: 10px;
    color: #606266;
    font-size: 13px;
  }

  .metric-item strong {
    color: #1f2d3d;
    font-size: 26px;
  }

  .tab-toolbar {
    display: flex;
    gap: 8px;
    margin-bottom: 10px;
  }

  .tab-toolbar.compact {
    margin-top: -2px;
  }

  .document-layout {
    display: grid;
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 14px;
  }

  .module-tree {
    border: 1px solid #e5e6eb;
    border-radius: 6px;
    background: #fff;
    overflow: hidden;
  }

  .tree-title {
    padding: 12px 14px;
    border-bottom: 1px solid #ebeef5;
    color: #1f2d3d;
    font-weight: 600;
  }

  .module-tree :deep(.el-menu) {
    border-right: 0;
  }

  .module-tree :deep(.el-menu-item) {
    height: 42px;
    line-height: 42px;
  }

  .document-main {
    min-width: 0;
  }

  .document-search {
    margin-bottom: 6px;
  }

  .document-title {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .knowledge-shell {
    padding: 14px;
  }

  .knowledge-status {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) 160px 160px auto;
    gap: 12px;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;
  }

  .knowledge-status strong {
    display: block;
    margin-top: 4px;
    color: #1f2d3d;
  }

  .muted {
    color: #909399;
    font-size: 12px;
  }
}

@media (max-width: 1100px) {
  .course-detail {
    .basic-grid,
    .document-layout,
    .knowledge-status {
      grid-template-columns: 1fr;
    }

    .detail-header {
      flex-direction: column;
    }

    .header-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
}
</style>
