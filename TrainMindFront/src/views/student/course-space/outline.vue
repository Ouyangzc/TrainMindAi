<template>
  <section class="outline-page">
    <div class="page-heading">
      <div><span>COURSE OUTLINE</span><h1>课程目录</h1><p>目录来自当前发布版本，不展示虚假的完成进度。</p></div>
      <el-tag v-if="outline" effect="plain">知识库 V{{ outline.versionNo }}</el-tag>
    </div>

    <div v-loading="loading" class="module-list">
      <el-alert v-if="loadError" title="课程目录加载失败" :description="loadError" type="error" :closable="false" show-icon>
        <template #default><el-button size="small" plain type="danger" @click="loadOutline">重新加载</el-button></template>
      </el-alert>
      <el-empty v-else-if="!loading && !outline?.modules.length" description="当前发布版本暂无课程内容" />
      <article v-for="(module, index) in outline?.modules || []" v-else :key="module.moduleId || 'public'" class="module-card">
        <div class="module-index">{{ String(index + 1).padStart(2, '0') }}</div>
        <div class="module-content">
          <div class="module-heading">
            <div><small>{{ module.moduleCode || 'PUBLIC' }}</small><h2>{{ module.moduleName }}</h2><p>{{ module.description || '本模块已发布学习资料' }}</p></div>
            <el-tag type="info" effect="plain">{{ module.documents.length }} 份资料</el-tag>
          </div>
          <div v-if="module.documents.length" class="module-documents">
            <button v-for="document in module.documents" :key="document.documentId" type="button" @click="openDocument(document)">
              <span class="file-badge" :class="`file-badge--${document.fileExt}`">{{ fileLabel(document.fileExt) }}</span>
              <span><strong>{{ document.title }}</strong><small>{{ document.originalFilename || '当前发布资料' }} · V{{ document.versionNo }}</small></span>
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import { getStudentCourseOutline } from '@/api/student'
import type { StudentCourseOutline, StudentPublishedDocument } from '@/types'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => Number(route.params.courseId))
const loading = ref(false)
const loadError = ref('')
const outline = ref<StudentCourseOutline>()
let sequence = 0

async function loadOutline() {
  const current = ++sequence
  loading.value = true
  loadError.value = ''
  try {
    const response = await getStudentCourseOutline(courseId.value)
    if (current === sequence) outline.value = response.data
  } catch (error) {
    if (current === sequence) loadError.value = error instanceof Error ? error.message : '请稍后重试。'
  } finally {
    if (current === sequence) loading.value = false
  }
}

function openDocument(document: StudentPublishedDocument) {
  if (document.fileExt?.toLowerCase() === 'pdf') {
    router.push(`/student/courses/${courseId.value}/documents/${document.documentId}/preview`)
  } else {
    router.push({ path: `/student/courses/${courseId.value}/library`, query: { documentId: document.documentId.toString() } })
  }
}

function fileLabel(ext?: string) { return (ext || 'FILE').toUpperCase().slice(0, 5) }

watch(() => route.params.courseId, loadOutline, { immediate: true })
</script>

<style scoped lang="scss">
.outline-page { max-width: 1100px; margin: 0 auto; }.page-heading { margin-bottom: 23px; display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }.page-heading span { color: #3978a8; font-size: 11px; font-weight: 700; letter-spacing: .14em; }.page-heading h1 { margin: 7px 0 5px; font-size: 26px; }.page-heading p { margin: 0; color: #748194; font-size: 14px; }.module-list { min-height: 380px; }.module-card { margin-bottom: 15px; padding: 22px; display: grid; grid-template-columns: 55px minmax(0, 1fr); gap: 15px; border: 1px solid #e1e7ee; border-radius: 16px; background: #fff; }.module-index { color: #a8b4c1; font-size: 22px; font-weight: 300; }.module-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }.module-heading small { color: #4380ad; font-size: 10px; letter-spacing: .08em; }.module-heading h2 { margin: 4px 0 5px; font-size: 18px; }.module-heading p { margin: 0; color: #7b8797; font-size: 13px; }.module-documents { margin-top: 17px; border-top: 1px solid #edf0f4; }.module-documents button { width: 100%; padding: 12px 4px; display: flex; align-items: center; gap: 12px; text-align: left; color: #536477; border: 0; border-bottom: 1px solid #f0f2f5; background: transparent; cursor: pointer; }.module-documents button:last-child { border-bottom: 0; }.module-documents button:hover { color: #316f9f; }.module-documents button > span:nth-child(2) { min-width: 0; flex: 1; }.module-documents strong, .module-documents small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.module-documents strong { font-size: 13px; }.module-documents small { margin-top: 4px; color: #929dab; font-size: 11px; }.file-badge { width: 39px; height: 32px; display: grid; place-items: center; color: #456b98; border-radius: 8px; background: #eaf2fb; font-size: 9px; font-weight: 700; }.file-badge--pdf { color: #b44e53; background: #fff0f0; }@media(max-width:600px){.module-card{padding:17px;grid-template-columns:1fr}.module-index{display:none}.page-heading p{display:none}}
</style>
