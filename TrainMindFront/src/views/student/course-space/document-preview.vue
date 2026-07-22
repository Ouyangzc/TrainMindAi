<template>
  <section class="preview-page">
    <header><el-button :icon="ArrowLeft" link @click="backToLibrary">返回资料库</el-button><div><h1>{{ document?.title || '资料预览' }}</h1><p v-if="document">{{ document.originalFilename }} · V{{ document.versionNo }}<span v-if="page"> · 定位第 {{ page }} 页</span></p></div><el-button v-if="allowDownload" :icon="Download" :loading="downloading" @click="downloadFile">下载</el-button></header>
    <el-alert v-if="loadError" title="资料预览失败" :description="loadError" type="error" show-icon :closable="false"><template #default><el-button size="small" type="danger" plain @click="loadPreview">重新加载</el-button></template></el-alert>
    <div v-loading="loading" class="preview-stage"><iframe v-if="previewUrl" :src="previewUrl" title="PDF 资料预览"></iframe><el-empty v-else-if="!loading && !loadError" description="当前资料无法在线预览" /></div>
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download } from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'
import { downloadStudentDocument, getMyCourse, getStudentDocument, previewStudentDocument, recordStudentActivity } from '@/api/student'
import type { StudentPublishedDocument } from '@/types'
const route=useRoute(),router=useRouter(),courseId=computed(()=>Number(route.params.courseId)),documentId=computed(()=>Number(route.params.documentId)),page=computed(()=>Number(route.query.page)||undefined)
const loading=ref(false),downloading=ref(false),loadError=ref(''),document=ref<StudentPublishedDocument>(),allowDownload=ref(false),previewUrl=ref('')
async function loadPreview(){loading.value=true;loadError.value='';releaseUrl();try{const [docResponse,courseResponse]=await Promise.all([getStudentDocument(courseId.value,documentId.value),getMyCourse(courseId.value)]);document.value=docResponse.data;allowDownload.value=Boolean(courseResponse.data?.allowDownload);if(document.value?.fileExt?.toLowerCase()!=='pdf')throw new Error('当前文件类型不支持在线预览');const blob=await previewStudentDocument(courseId.value,documentId.value);const objectUrl=URL.createObjectURL(blob);previewUrl.value=page.value?`${objectUrl}#page=${page.value}`:objectUrl;recordStudentActivity(courseId.value,'document_view',documentId.value).catch(()=>undefined)}catch(error){loadError.value=error instanceof Error?error.message:'请稍后重试。'}finally{loading.value=false}}
async function downloadFile(){if(!document.value)return;downloading.value=true;try{const blob=await downloadStudentDocument(courseId.value,documentId.value);saveAs(blob,document.value.originalFilename||document.value.title)}catch{ElMessage.error('资料下载失败')}finally{downloading.value=false}}
function backToLibrary(){router.push({path:`/student/courses/${courseId.value}/library`,query:{documentId:documentId.value.toString(),...(page.value?{page:page.value.toString()}:{})}})}
function releaseUrl(){if(previewUrl.value){URL.revokeObjectURL(previewUrl.value.split('#')[0]);previewUrl.value=''}}
watch(()=>[route.params.courseId,route.params.documentId,route.query.page],loadPreview,{immediate:true});onBeforeUnmount(releaseUrl)
</script>

<style scoped lang="scss">
.preview-page{max-width:1280px;margin:0 auto}.preview-page header{min-height:60px;margin-bottom:15px;padding:12px 16px;display:grid;grid-template-columns:130px minmax(0,1fr) 110px;align-items:center;gap:14px;border:1px solid #e1e7ee;border-radius:13px;background:#fff}.preview-page header h1{margin:0 0 4px;overflow:hidden;font-size:16px;text-overflow:ellipsis;white-space:nowrap}.preview-page header p{margin:0;color:#8b96a5;font-size:11px}.preview-stage{height:calc(100vh - 245px);min-height:520px;overflow:hidden;border:1px solid #dce3eb;border-radius:13px;background:#e9edf2}.preview-stage iframe{width:100%;height:100%;border:0;background:#fff}@media(max-width:650px){.preview-page header{grid-template-columns:auto minmax(0,1fr)}.preview-page header>.el-button:last-child{display:none}.preview-stage{height:calc(100vh - 230px);min-height:430px}}
</style>
