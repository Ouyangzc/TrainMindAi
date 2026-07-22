<template>
  <section class="section-shell">
    <div class="section-kicker">{{ sectionMeta.kicker }}</div>
    <div class="section-heading">
      <div>
        <h1>{{ sectionMeta.title }}</h1>
        <p>{{ sectionMeta.description }}</p>
      </div>
      <el-tag effect="plain">课程上下文已连接</el-tag>
    </div>
    <el-card shadow="never" class="section-pending">
      <el-empty :description="sectionMeta.pending">
        <el-button v-if="section !== 'assistant'" type="primary" plain @click="goAssistant">
          返回 AI 学习助教
        </el-button>
      </el-empty>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

type StudentSection = 'assistant' | 'outline' | 'library' | 'activities'
const route = useRoute()
const router = useRouter()
const section = computed(() => (route.meta.studentSection || 'assistant') as StudentSection)
const meta = {
  assistant: { kicker: 'COURSE AI', title: 'AI 学习助教', description: '回答将仅依据当前课程已发布资料。', pending: '问答界面将在下一项任务接入' },
  outline: { kicker: 'COURSE OUTLINE', title: '课程目录', description: '按课程模块查看当前发布的学习资料。', pending: '课程目录内容将在后续任务接入' },
  library: { kicker: 'COURSE LIBRARY', title: '资料库', description: '搜索和查阅当前课程的有效资料版本。', pending: '资料检索内容将在后续任务接入' },
  activities: { kicker: 'LEARNING RECORD', title: '学习记录', description: '记录课程内真实发生的查阅和问答活动。', pending: '尚未产生学习记录' }
}
const sectionMeta = computed(() => meta[section.value as StudentSection])

function goAssistant() {
  router.push(`/student/courses/${route.params.courseId}/assistant`)
}
</script>

<style scoped lang="scss">
.section-shell { max-width: 1180px; margin: 0 auto; }
.section-kicker { color: #3978a8; font-size: 11px; font-weight: 700; letter-spacing: 0.14em; }
.section-heading { margin: 8px 0 22px; display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }
.section-heading h1 { margin: 0 0 6px; font-size: 26px; }
.section-heading p { margin: 0; color: #748194; font-size: 14px; }
.section-pending { min-height: 390px; display: grid; place-items: center; border-radius: 16px; }
@media (max-width: 600px) { .section-heading { align-items: flex-start; flex-direction: column; } }
</style>
