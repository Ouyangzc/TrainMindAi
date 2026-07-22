<template>
  <div class="student-courses-page">
    <section class="hero-panel">
      <div>
        <span class="eyebrow">TRAINMIND LEARNING</span>
        <h1>我的课程</h1>
        <p>从课程开始学习，遇到问题时向课程知识助教提问。</p>
      </div>
      <div class="hero-summary">
        <strong>{{ availableCourses.length }}</strong>
        <span>门课程可学习</span>
      </div>
    </section>

    <main v-loading="loading" class="courses-content">
      <el-alert
        v-if="loadError"
        title="课程加载失败"
        :description="loadError"
        type="error"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button type="danger" plain size="small" @click="loadCourses">重新加载</el-button>
        </template>
      </el-alert>

      <el-empty
        v-else-if="!loading && courses.length === 0"
        description="暂时没有向你开放的课程"
      >
        <p class="empty-hint">课程由培训管理员授权，获得授权后会出现在这里。</p>
      </el-empty>

      <template v-else>
        <section v-if="availableCourses.length" class="course-section">
          <div class="section-heading">
            <div>
              <h2>继续学习</h2>
              <p>已发布课程内容，可以进入课程空间学习和提问。</p>
            </div>
            <span>{{ availableCourses.length }} 门</span>
          </div>
          <div class="course-grid">
            <article
              v-for="(course, index) in availableCourses"
              :key="course.courseId"
              class="course-card course-card--available"
            >
              <div class="course-cover" :class="`course-cover--${index % 4}`">
                <span>{{ course.courseCategory || '课程学习' }}</span>
                <strong>{{ course.courseName.slice(0, 1) }}</strong>
                <small>知识库 V{{ course.publishedVersionNo }}</small>
              </div>
              <div class="course-card__body">
                <div class="course-code">{{ course.courseCode }}</div>
                <h3>{{ course.courseName }}</h3>
                <p>{{ course.description || '进入课程空间，查看目录、资料并向知识助教提问。' }}</p>
                <div class="course-meta">
                  <span><el-icon><User /></el-icon>{{ course.ownerName || '课程负责人' }}</span>
                  <span v-if="course.lastVisitedAt"><el-icon><Clock /></el-icon>最近 {{ formatRecent(course.lastVisitedAt) }}</span>
                  <span v-else-if="course.accessEndAt"><el-icon><Calendar /></el-icon>至 {{ formatDate(course.accessEndAt) }}</span>
                </div>
                <el-button type="primary" class="enter-button" @click="enterCourse(course)">
                  进入课程 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
                </el-button>
              </div>
            </article>
          </div>
        </section>

        <section v-if="unavailableCourses.length" class="course-section course-section--muted">
          <div class="section-heading">
            <div>
              <h2>其他课程</h2>
              <p>这些课程暂时不能进入学习，状态变化后会自动开放。</p>
            </div>
            <span>{{ unavailableCourses.length }} 门</span>
          </div>
          <div class="course-grid">
            <article
              v-for="course in unavailableCourses"
              :key="course.courseId"
              class="course-card course-card--disabled"
            >
              <div class="status-strip" :class="`status-strip--${course.availability}`"></div>
              <div class="course-card__body">
                <div class="card-topline">
                  <div class="course-code">{{ course.courseCode }}</div>
                  <el-tag :type="statusMeta[course.availability].tagType" effect="light">
                    {{ statusMeta[course.availability].label }}
                  </el-tag>
                </div>
                <h3>{{ course.courseName }}</h3>
                <p>{{ statusDescription(course) }}</p>
                <div class="course-meta">
                  <span><el-icon><User /></el-icon>{{ course.ownerName || '课程负责人' }}</span>
                  <span v-if="course.courseCategory">{{ course.courseCategory }}</span>
                </div>
                <el-button disabled class="enter-button">暂不可进入</el-button>
              </div>
            </article>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowRight, Calendar, Clock, User } from '@element-plus/icons-vue'
import { listMyCourses } from '@/api/student'
import type { StudentCourse, StudentCourseAvailability } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadError = ref('')
const courses = ref<StudentCourse[]>([])

type CourseTagType = 'success' | 'warning' | 'info' | 'danger'

const statusMeta: Record<StudentCourseAvailability, { label: string; tagType: CourseTagType }> = {
  available: { label: '可学习', tagType: 'success' },
  content_preparing: { label: '内容准备中', tagType: 'warning' },
  not_started: { label: '尚未开始', tagType: 'info' },
  expired: { label: '已到期', tagType: 'info' },
  access_disabled: { label: '授权已停用', tagType: 'danger' },
  course_disabled: { label: '课程已停用', tagType: 'danger' }
}

const availableCourses = computed(() => courses.value.filter(
  (item: StudentCourse) => item.availability === 'available'
))
const unavailableCourses = computed(() => courses.value.filter(
  (item: StudentCourse) => item.availability !== 'available'
))

async function loadCourses() {
  loading.value = true
  loadError.value = ''
  try {
    const response = await listMyCourses()
    courses.value = response.data || []
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '请检查网络连接后重试。'
  } finally {
    loading.value = false
  }
}

function enterCourse(course: StudentCourse) {
  router.push(`/student/courses/${course.courseId}/assistant`)
}

function formatDate(value: string) {
  return value.slice(0, 10)
}

function formatRecent(value: string) {
  const date = new Date(value.replace(' ', 'T'))
  const now = new Date()
  const sameDay = date.toDateString() === now.toDateString()
  return sameDay
    ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : value.slice(5, 16)
}

function statusDescription(course: StudentCourse) {
  switch (course.availability) {
    case 'content_preparing':
      return '课程负责人正在整理和发布学习资料。'
    case 'not_started':
      return course.accessStartAt ? `将于 ${formatDate(course.accessStartAt)} 开放学习。` : '课程尚未开放学习。'
    case 'expired':
      return course.accessEndAt ? `学习授权已于 ${formatDate(course.accessEndAt)} 到期。` : '课程学习授权已到期。'
    case 'access_disabled':
      return '你的课程授权已暂停，如有疑问请联系课程负责人。'
    case 'course_disabled':
      return '课程当前处于停用状态。'
    default:
      return course.description || '课程暂时不能进入。'
  }
}

onMounted(loadCourses)
</script>

<style scoped lang="scss">
.student-courses-page {
  min-height: calc(100vh - 84px);
  padding: 28px clamp(18px, 4vw, 56px) 56px;
  color: #172033;
  background:
    radial-gradient(circle at 88% -5%, rgba(64, 158, 255, 0.16), transparent 30%),
    #f5f7fb;
}

.hero-panel {
  max-width: 1440px;
  margin: 0 auto 30px;
  padding: 30px 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  color: #fff;
  border-radius: 22px;
  background: linear-gradient(125deg, #172d55 0%, #205ea6 62%, #3c8bd7 100%);
  box-shadow: 0 18px 45px rgba(23, 57, 101, 0.18);

  .eyebrow { font-size: 12px; letter-spacing: 0.18em; color: #9fd2ff; }
  h1 { margin: 8px 0 7px; font-size: 32px; font-weight: 650; }
  p { margin: 0; color: rgba(255, 255, 255, 0.76); }
}

.hero-summary {
  min-width: 150px;
  padding: 12px 22px;
  text-align: center;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  strong { display: block; font-size: 36px; line-height: 1; }
  span { display: block; margin-top: 8px; color: #c5e4ff; font-size: 13px; }
}

.courses-content { max-width: 1440px; min-height: 300px; margin: 0 auto; }
.course-section + .course-section { margin-top: 38px; }
.section-heading {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  h2 { margin: 0 0 5px; font-size: 21px; }
  p { margin: 0; color: #7b8496; font-size: 14px; }
  > span { color: #8892a4; font-size: 13px; }
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 20px;
}

.course-card {
  position: relative;
  overflow: hidden;
  border: 1px solid #e5e9f1;
  border-radius: 16px;
  background: #fff;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.course-card--available:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 38px rgba(39, 72, 117, 0.13);
}
.course-cover {
  height: 126px;
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  color: #fff;
  background: linear-gradient(135deg, #245ba2, #43a1c7);
  &::after {
    content: '';
    position: absolute;
    width: 150px;
    height: 150px;
    right: -40px;
    top: -70px;
    border: 24px solid rgba(255, 255, 255, 0.09);
    border-radius: 50%;
  }
  span { font-size: 12px; opacity: 0.8; }
  strong { display: block; margin-top: 13px; font-size: 34px; font-weight: 500; }
  small { position: absolute; right: 18px; bottom: 15px; opacity: 0.78; }
}
.course-cover--1 { background: linear-gradient(135deg, #4253a8, #7b70d3); }
.course-cover--2 { background: linear-gradient(135deg, #176b69, #43a886); }
.course-cover--3 { background: linear-gradient(135deg, #9a572a, #d59043); }

.course-card__body { padding: 20px; }
.course-code { color: #8290a5; font-size: 12px; letter-spacing: 0.05em; }
.course-card h3 { min-height: 48px; margin: 7px 0 8px; font-size: 18px; line-height: 1.35; }
.course-card p {
  min-height: 42px;
  margin: 0;
  overflow: hidden;
  color: #6d7789;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.course-meta {
  min-height: 45px;
  margin: 17px 0;
  padding-top: 13px;
  display: flex;
  flex-wrap: wrap;
  gap: 7px 16px;
  color: #7c8799;
  font-size: 12px;
  border-top: 1px solid #edf0f5;
  span { display: inline-flex; align-items: center; gap: 5px; }
}
.enter-button { width: 100%; }
.card-topline { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.course-card--disabled { background: #fafbfc; }
.status-strip { height: 5px; background: #a6afbc; }
.status-strip--content_preparing { background: #e6a23c; }
.status-strip--access_disabled, .status-strip--course_disabled { background: #d66a70; }
.empty-hint { margin: -18px 0 0; color: #929bad; font-size: 13px; }

@media (max-width: 700px) {
  .student-courses-page { padding: 16px 14px 40px; }
  .hero-panel { padding: 24px 22px; border-radius: 16px; }
  .hero-panel h1 { font-size: 27px; }
  .hero-summary { min-width: 92px; padding: 8px 0 8px 16px; }
  .hero-summary strong { font-size: 30px; }
  .course-grid { grid-template-columns: 1fr; }
}
</style>
