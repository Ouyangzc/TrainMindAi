<template>
  <section class="activities-page">
    <div class="page-heading">
      <div><span>LEARNING RECORD</span><h1>学习记录</h1><p>这里只记录真实发生的课程访问、资料查阅和 AI 问答。</p></div>
      <el-button :icon="Refresh" plain :loading="loading" @click="loadActivities">刷新</el-button>
    </div>
    <el-alert v-if="loadError" title="学习记录加载失败" :description="loadError" type="error" show-icon :closable="false" />
    <div v-loading="loading" class="timeline-card">
      <el-empty v-if="!loading && !activities.length && !loadError" description="还没有学习活动" />
      <el-timeline v-else>
        <el-timeline-item
          v-for="activity in activities"
          :key="activity.id"
          :timestamp="formatTime(activity.occurredAt)"
          placement="top"
          :type="activityMeta[activity.activityType].type"
          :hollow="activity.activityType === 'course_view'"
        >
          <article class="activity-item">
            <div class="activity-icon" :class="`activity-icon--${activity.activityType}`">
              <el-icon><component :is="activityMeta[activity.activityType].icon" /></el-icon>
            </div>
            <div>
              <small>{{ activityMeta[activity.activityType].label }}</small>
              <h2>{{ activity.targetTitle || activityMeta[activity.activityType].fallback }}</h2>
              <p v-if="activity.targetDetail">{{ activity.targetDetail }}</p>
            </div>
            <el-button
              v-if="activity.activityType === 'document_view' && activity.targetId"
              link
              type="primary"
              @click="openDocument(activity.targetId)"
            >再次查看</el-button>
            <el-button
              v-else-if="activity.activityType === 'chat'"
              link
              type="primary"
              @click="openAssistant"
            >查看对话</el-button>
          </article>
        </el-timeline-item>
      </el-timeline>
    </div>
    <p class="record-note"><el-icon><InfoFilled /></el-icon>学习记录不代表课程完成度，也不用于推算强制学习时长。</p>
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Collection, FolderOpened, InfoFilled, Refresh, View } from '@element-plus/icons-vue'
import { listStudentActivities } from '@/api/student'
import type { StudentLearningActivity, StudentLearningActivityType } from '@/types'

const route = useRoute(), router = useRouter(), courseId = computed(() => Number(route.params.courseId))
const loading = ref(false), loadError = ref(''), activities = ref<StudentLearningActivity[]>([])
const activityMeta: Record<StudentLearningActivityType, { label: string; fallback: string; type: 'primary' | 'success' | 'warning' | 'info'; icon: object }> = {
  course_view: { label: '课程访问', fallback: '进入课程空间', type: 'info', icon: View },
  module_view: { label: '课程目录', fallback: '查看课程模块', type: 'primary', icon: Collection },
  document_view: { label: '资料查阅', fallback: '查看课程资料', type: 'success', icon: FolderOpened },
  chat: { label: 'AI 问答', fallback: '向 AI 学习助教提问', type: 'warning', icon: ChatDotRound }
}
let sequence = 0
async function loadActivities(){const current=++sequence;loading.value=true;loadError.value='';try{const response=await listStudentActivities(courseId.value);if(current===sequence)activities.value=response.data||[]}catch(error){if(current===sequence)loadError.value=error instanceof Error?error.message:'请稍后重试。'}finally{if(current===sequence)loading.value=false}}
function formatTime(value:string){return value.slice(0,16)}
function openDocument(documentId:number){router.push(`/student/courses/${courseId.value}/documents/${documentId}/preview`)}
function openAssistant(){router.push(`/student/courses/${courseId.value}/assistant`)}
watch(()=>route.params.courseId,loadActivities,{immediate:true})
</script>

<style scoped lang="scss">
.activities-page{max-width:1000px;margin:0 auto}.page-heading{margin-bottom:22px;display:flex;align-items:flex-end;justify-content:space-between;gap:20px}.page-heading span{color:#3978a8;font-size:11px;font-weight:700;letter-spacing:.14em}.page-heading h1{margin:7px 0 5px;font-size:26px}.page-heading p{margin:0;color:#748194;font-size:14px}.timeline-card{min-height:380px;padding:28px 30px 10px;border:1px solid #e1e7ee;border-radius:16px;background:#fff}.activity-item{margin-top:-4px;padding:14px 16px;display:flex;align-items:center;gap:13px;border:1px solid #e9edf2;border-radius:12px;background:#fbfcfe}.activity-icon{width:38px;height:38px;flex:0 0 auto;display:grid;place-items:center;color:#46739c;border-radius:10px;background:#eaf2f9}.activity-icon--document_view{color:#27816f;background:#e8f7f2}.activity-icon--chat{color:#785bbb;background:#f0ecfb}.activity-item>div:nth-child(2){min-width:0;flex:1}.activity-item small{color:#8c98a7;font-size:10px}.activity-item h2{margin:3px 0;font-size:14px}.activity-item p{margin:0;overflow:hidden;color:#7d8998;font-size:12px;text-overflow:ellipsis;white-space:nowrap}.record-note{display:flex;align-items:center;gap:6px;color:#929caa;font-size:11px}@media(max-width:600px){.page-heading p{display:none}.timeline-card{padding:22px 13px 5px}.activity-item{padding:12px}.activity-item>.el-button{display:none}}
</style>
