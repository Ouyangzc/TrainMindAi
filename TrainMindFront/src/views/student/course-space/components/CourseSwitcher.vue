<template>
  <el-select
    :model-value="courseId"
    class="course-switcher"
    placeholder="选择课程"
    :loading="loading"
    @change="handleChange"
  >
    <el-option
      v-for="course in courses"
      :key="course.courseId"
      :label="course.courseName"
      :value="course.courseId"
      :disabled="course.availability !== 'available'"
    >
      <div class="course-option">
        <span>{{ course.courseName }}</span>
        <small>{{ course.courseCode }}</small>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import type { StudentCourse } from '@/types'

defineProps<{
  courseId: number
  courses: StudentCourse[]
  loading: boolean
}>()

const emit = defineEmits<{
  change: [courseId: number]
}>()

function handleChange(value: number) {
  emit('change', value)
}
</script>

<style scoped lang="scss">
.course-switcher { width: min(360px, 38vw); }
.course-option { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.course-option small { color: #98a2b3; }
@media (max-width: 700px) { .course-switcher { width: 100%; } }
</style>
