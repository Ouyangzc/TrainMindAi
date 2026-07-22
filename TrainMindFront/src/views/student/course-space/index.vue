<template>
  <div class="course-space">
    <header class="course-space__topbar">
      <button class="back-link" type="button" @click="router.push('/student/courses')">
        <el-icon><ArrowLeft /></el-icon><span>我的课程</span>
      </button>
      <CourseSwitcher
        :course-id="courseId"
        :courses="availableCourses"
        :loading="loading"
        @change="switchCourse"
      />
      <div class="version-state" :class="{ 'version-state--loading': loading }">
        <i></i>
        <span>{{ versionLabel }}</span>
      </div>
    </header>

    <div v-if="loadError" class="course-space__error">
      <el-result icon="error" title="无法进入课程" :sub-title="loadError">
        <template #extra>
          <el-button type="primary" @click="loadContext">重新加载</el-button>
          <el-button @click="router.push('/student/courses')">返回我的课程</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="course-space__layout">
      <aside class="course-nav">
        <div class="course-identity">
          <span>{{ currentCourse?.courseCategory || '课程学习' }}</span>
          <strong>{{ currentCourse?.courseName || '正在加载课程…' }}</strong>
          <small>{{ currentCourse?.courseCode }}</small>
        </div>

        <nav aria-label="课程空间导航">
          <router-link
            v-for="item in navigation"
            :key="item.section"
            :to="sectionPath(item.section)"
            class="nav-item"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="scope-note">
          <el-icon><Lock /></el-icon>
          <div>
            <strong>课程内容已隔离</strong>
            <span>问答和资料仅来自当前课程发布版本</span>
          </div>
        </div>
      </aside>

      <main v-loading="loading" class="course-workspace">
        <router-view v-if="currentCourse" :key="`${courseId}-${activeSection}`" />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ChatDotRound, Clock, Collection, FolderOpened, Lock } from '@element-plus/icons-vue'
import CourseSwitcher from './components/CourseSwitcher.vue'
import { listMyCourses, recordStudentActivity } from '@/api/student'
import type { StudentCourse } from '@/types'

type StudentSection = 'assistant' | 'outline' | 'library' | 'activities'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const courses = ref<StudentCourse[]>([])
const currentCourse = ref<StudentCourse>()
let requestSequence = 0

const navigation = [
  { section: 'assistant' as const, label: 'AI 学习助教', icon: ChatDotRound },
  { section: 'outline' as const, label: '课程目录', icon: Collection },
  { section: 'library' as const, label: '资料库', icon: FolderOpened },
  { section: 'activities' as const, label: '学习记录', icon: Clock }
]

const courseId = computed(() => Number(route.params.courseId))
const activeSection = computed(() => (route.meta.studentSection || 'assistant') as StudentSection)
const availableCourses = computed(() => courses.value.filter(
  (item: StudentCourse) => item.availability === 'available'
))
const versionLabel = computed(() => currentCourse.value?.publishedVersionNo
  ? `知识库 V${currentCourse.value.publishedVersionNo}`
  : '正在确认知识库版本')

async function loadContext() {
  const sequence = ++requestSequence
  loading.value = true
  loadError.value = ''
  currentCourse.value = undefined
  try {
    if (!Number.isSafeInteger(courseId.value) || courseId.value <= 0) {
      throw new Error('课程地址无效')
    }
    const response = await listMyCourses()
    if (sequence !== requestSequence) return
    courses.value = response.data || []
    const matched = courses.value.find((item: StudentCourse) => item.courseId === courseId.value)
    if (!matched) throw new Error('课程不存在或未向当前学员授权')
    if (matched.availability !== 'available') throw new Error('当前课程暂时不可进入学习')
    currentCourse.value = matched
    recordStudentActivity(courseId.value, 'course_view', courseId.value).catch(() => undefined)
  } catch (error) {
    if (sequence !== requestSequence) return
    loadError.value = error instanceof Error ? error.message : '课程加载失败，请稍后重试。'
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

function sectionPath(section: StudentSection, targetCourseId = courseId.value) {
  return `/student/courses/${targetCourseId}/${section}`
}

function switchCourse(targetCourseId: number) {
  if (targetCourseId === courseId.value) return
  requestSequence++
  currentCourse.value = undefined
  ElMessage.success('已切换课程')
  router.push(sectionPath(activeSection.value, targetCourseId))
}

watch(() => route.params.courseId, loadContext, { immediate: true })
</script>

<style scoped lang="scss">
.course-space { min-height: calc(100vh - 84px); color: #172033; background: #f4f7fa; }
.course-space__topbar {
  height: 68px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  background: #fff;
  border-bottom: 1px solid #e6eaf0;
}
.back-link {
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #536274;
  border: 0;
  background: transparent;
  cursor: pointer;
}
.version-state { margin-left: auto; display: flex; align-items: center; gap: 8px; color: #25816f; font-size: 12px; }
.version-state i { width: 7px; height: 7px; border-radius: 50%; background: #25b790; box-shadow: 0 0 0 4px #e5f7f2; }
.version-state--loading i { background: #aab3c0; box-shadow: 0 0 0 4px #f0f2f5; }
.course-space__layout { display: grid; grid-template-columns: 238px minmax(0, 1fr); min-height: calc(100vh - 152px); }
.course-nav { padding: 25px 16px; display: flex; flex-direction: column; color: #c1d1dd; background: #132f46; }
.course-identity { padding: 2px 12px 23px; border-bottom: 1px solid rgba(255, 255, 255, 0.09); }
.course-identity span { color: #6fa3be; font-size: 11px; }
.course-identity strong { margin: 7px 0 5px; display: block; color: #fff; line-height: 1.45; }
.course-identity small { color: #7893a7; }
.course-nav nav { margin-top: 19px; }
.nav-item { margin: 5px 0; padding: 12px; display: flex; align-items: center; gap: 11px; border-radius: 10px; font-size: 14px; }
.nav-item:hover, .nav-item.router-link-active { color: #fff; background: #1e4a64; }
.scope-note { margin-top: auto; padding: 14px 12px; display: flex; gap: 9px; border: 1px solid #28526a; border-radius: 12px; }
.scope-note strong, .scope-note span { display: block; }
.scope-note strong { color: #fff; font-size: 12px; }
.scope-note span { margin-top: 4px; color: #7899ad; font-size: 11px; line-height: 1.5; }
.course-workspace { min-width: 0; min-height: 520px; padding: 30px clamp(20px, 4vw, 46px); }
.course-space__error { padding-top: 60px; }

@media (max-width: 760px) {
  .course-space__topbar { height: auto; min-height: 68px; padding: 12px 14px; flex-wrap: wrap; gap: 10px 16px; }
  .back-link span, .version-state { display: none; }
  .course-space__layout { display: block; min-height: calc(100vh - 120px); }
  .course-nav { padding: 8px 10px; display: block; overflow-x: auto; white-space: nowrap; }
  .course-identity, .scope-note { display: none; }
  .course-nav nav { margin: 0; display: flex; gap: 5px; }
  .nav-item { flex: 0 0 auto; margin: 0; padding: 10px 12px; }
  .course-workspace { padding: 22px 15px; }
}
</style>
