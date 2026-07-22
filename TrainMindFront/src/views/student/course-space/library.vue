<template>
  <section class="library-page">
    <div class="page-heading"><div><span>COURSE LIBRARY</span><h1>课程资料库</h1><p>仅展示当前课程当前发布版本中的资料。</p></div><el-tag effect="plain">{{ total }} 份资料</el-tag></div>
    <el-form class="library-toolbar" inline @submit.prevent="search">
      <el-form-item><el-input v-model="query.keyword" clearable :prefix-icon="Search" placeholder="搜索资料名称" @keyup.enter="search" @clear="search" /></el-form-item>
      <el-form-item><el-select v-model="query.moduleId" clearable placeholder="全部模块" @change="search"><el-option v-for="module in modules" :key="module.moduleId" :label="module.moduleName" :value="module.moduleId" /></el-select></el-form-item>
      <el-form-item><el-select v-model="query.fileExt" clearable placeholder="全部类型" @change="search"><el-option v-for="ext in fileTypes" :key="ext" :label="ext.toUpperCase()" :value="ext" /></el-select></el-form-item>
      <el-form-item><el-button type="primary" :icon="Search" @click="search">查询</el-button><el-button :icon="Refresh" @click="resetFilters">重置</el-button></el-form-item>
    </el-form>
    <el-alert v-if="loadError" title="资料加载失败" :description="loadError" type="error" show-icon :closable="false" />
    <div v-loading="loading" class="document-list">
      <el-empty v-if="!loading && !documents.length && !loadError" description="没有符合条件的已发布资料" />
      <article v-for="document in documents" :key="document.documentId" :class="{ 'document-card--target': document.documentId === targetDocumentId }" class="document-card">
        <div class="file-icon" :class="`file-icon--${document.fileExt}`">{{ fileLabel(document.fileExt) }}</div>
        <div class="document-info"><div><el-tag v-if="document.documentId === targetDocumentId" size="small" type="warning">AI 引用</el-tag><span>{{ document.moduleName || '通用资料' }}</span></div><h2>{{ document.title }}</h2><p>{{ document.originalFilename || '当前发布资料' }}</p></div>
        <div class="document-version"><span>当前有效版本</span><strong>V{{ document.versionNo }}</strong><small>{{ formatSize(document.fileSize) }}</small></div>
        <div class="document-actions"><el-button v-if="document.fileExt?.toLowerCase() === 'pdf'" type="primary" link @click="preview(document)">在线预览</el-button><el-button v-if="allowDownload" link :loading="downloadingId === document.documentId" @click="downloadDocument(document)">下载</el-button><span v-else class="download-disabled">课程未开放下载</span></div>
      </article>
    </div>
    <pagination v-show="total > 0" v-model:page="query.pageNum" v-model:limit="query.pageSize" :total="total" @pagination="loadDocuments()" />
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'
import { downloadStudentDocument, getMyCourse, getStudentCourseOutline, getStudentDocument, listStudentDocuments } from '@/api/student'
import type { StudentCourseModule, StudentDocumentQuery, StudentPublishedDocument } from '@/types'

const route = useRoute(), router = useRouter()
const courseId = computed(() => Number(route.params.courseId))
const loading = ref(false), loadError = ref(''), documents = ref<StudentPublishedDocument[]>([]), modules = ref<StudentCourseModule[]>([]), total = ref(0), allowDownload = ref(false), downloadingId = ref<number>()
const targetDocumentId = computed(() => Number(route.query.documentId) || undefined)
const query = reactive<StudentDocumentQuery>({ pageNum: 1, pageSize: 10, keyword: undefined, moduleId: undefined, fileExt: undefined })
const fileTypes = ['pdf', 'docx', 'pptx', 'xlsx']
let sequence = 0

async function initialize() {
  const current = ++sequence
  loading.value = true; loadError.value = ''
  try {
    const [courseResponse, outlineResponse] = await Promise.all([getMyCourse(courseId.value), getStudentCourseOutline(courseId.value)])
    if (current !== sequence) return
    allowDownload.value = Boolean(courseResponse.data?.allowDownload)
    modules.value = (outlineResponse.data?.modules || []).filter((item: StudentCourseModule) => item.moduleId != null)
    if (targetDocumentId.value) {
      const target = await getStudentDocument(courseId.value, targetDocumentId.value)
      if (current !== sequence) return
      query.keyword = target.data?.title
    }
    await loadDocuments(current)
  } catch (error) {
    if (current === sequence) loadError.value = error instanceof Error ? error.message : '请稍后重试。'
  } finally { if (current === sequence) loading.value = false }
}

async function loadDocuments(expectedSequence = sequence) {
  loading.value = true; loadError.value = ''
  try { const response = await listStudentDocuments(courseId.value, query); if (expectedSequence !== sequence) return; documents.value = response.rows || []; total.value = response.total || 0 }
  catch (error) { if (expectedSequence === sequence) loadError.value = error instanceof Error ? error.message : '请稍后重试。' }
  finally { if (expectedSequence === sequence) loading.value = false }
}
function search() { query.pageNum = 1; router.replace({ query: {} }); loadDocuments() }
function resetFilters() { Object.assign(query, { pageNum: 1, keyword: undefined, moduleId: undefined, fileExt: undefined }); router.replace({ query: {} }); loadDocuments() }
function preview(document: StudentPublishedDocument) { router.push({ path: `/student/courses/${courseId.value}/documents/${document.documentId}/preview`, query: targetDocumentId.value === document.documentId && route.query.page ? { page: route.query.page } : {} }) }
async function downloadDocument(document: StudentPublishedDocument) { downloadingId.value = document.documentId; try { const blob = await downloadStudentDocument(courseId.value, document.documentId); saveAs(blob, document.originalFilename || document.title); } catch { ElMessage.error('资料下载失败') } finally { downloadingId.value = undefined } }
function fileLabel(ext?: string) { return (ext || 'FILE').toUpperCase().slice(0, 5) }
function formatSize(size?: number) { if (!size) return ''; if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`; return `${(size / 1024 / 1024).toFixed(1)} MB` }
watch(() => route.params.courseId, initialize, { immediate: true })
</script>

<style scoped lang="scss">
.library-page{max-width:1180px;margin:0 auto}.page-heading{margin-bottom:21px;display:flex;align-items:flex-end;justify-content:space-between;gap:20px}.page-heading span{color:#3978a8;font-size:11px;font-weight:700;letter-spacing:.14em}.page-heading h1{margin:7px 0 5px;font-size:26px}.page-heading p{margin:0;color:#748194;font-size:14px}.library-toolbar{padding:16px 17px 0;border:1px solid #e2e7ee;border-radius:14px;background:#fff}.library-toolbar :deep(.el-input){width:260px}.library-toolbar :deep(.el-select){width:150px}.document-list{min-height:320px;margin-top:15px}.document-card{margin-bottom:10px;padding:16px 18px;display:grid;grid-template-columns:52px minmax(220px,1fr) 130px 160px;align-items:center;gap:15px;border:1px solid #e1e7ee;border-radius:13px;background:#fff}.document-card--target{border-color:#e6b75c;box-shadow:0 0 0 3px #fff4d9}.file-icon{width:43px;height:45px;display:grid;place-items:center;color:#436d99;border-radius:10px;background:#eaf2fb;font-size:10px;font-weight:800}.file-icon--pdf{color:#b44950;background:#fff0f0}.document-info>div{display:flex;align-items:center;gap:8px}.document-info>div span{color:#8995a4;font-size:11px}.document-info h2{margin:5px 0 3px;overflow:hidden;font-size:14px;text-overflow:ellipsis;white-space:nowrap}.document-info p{margin:0;color:#929caa;font-size:11px}.document-version span,.document-version strong,.document-version small{display:block}.document-version span{color:#929dab;font-size:10px}.document-version strong{margin:3px 0;color:#278270;font-size:13px}.document-version small{color:#9ba5b2;font-size:10px}.document-actions{text-align:right}.download-disabled{display:block;color:#a2aab5;font-size:11px}.library-page :deep(.pagination-container){background:transparent}@media(max-width:850px){.document-card{grid-template-columns:44px minmax(0,1fr) 110px}.document-version{display:none}.library-toolbar :deep(.el-input),.library-toolbar :deep(.el-select){width:100%}}@media(max-width:560px){.page-heading p{display:none}.document-card{grid-template-columns:40px minmax(0,1fr)}.document-actions{grid-column:2;text-align:left}.library-toolbar :deep(.el-form-item){width:100%;margin-right:0}}
</style>
