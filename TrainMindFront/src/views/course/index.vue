<template>
  <div class="app-container course-page">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="课程名称" prop="courseName">
        <el-input
          v-model="queryParams.courseName"
          placeholder="请输入课程名称或编码"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="课程分类" prop="courseCategory">
        <el-select v-model="queryParams.courseCategory" placeholder="课程分类" clearable style="width: 200px">
          <el-option label="航空维修培训" value="航空维修培训" />
          <el-option label="通用安全课程" value="通用安全课程" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="课程状态" clearable style="width: 160px">
          <el-option
            v-for="item in courseStatusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button v-hasPermi="['course:course:add']" type="primary" plain icon="Plus" @click="openCourseDialog()">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button v-hasPermi="['course:course:edit']" type="success" plain icon="Edit" :disabled="single" @click="editSelectedCourse">修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button v-hasPermi="['course:course:remove']" type="danger" plain icon="Delete" :disabled="multiple" @click="removeCourses()">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="handleQuery" />
    </el-row>

    <div class="course-summary">
      <div class="summary-item">
        <span class="summary-label">课程总数</span>
        <strong>{{ total }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">启用课程</span>
        <strong>{{ activeCourseCount }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">资料总数</span>
        <strong>{{ documentTotal }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">学员授权</span>
        <strong>{{ studentTotal }}</strong>
      </div>
    </div>

    <el-table v-loading="loading" :data="courseList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="课程编码" prop="courseCode" width="130" />
      <el-table-column label="课程名称" min-width="230" :show-overflow-tooltip="true">
        <template #default="scope">
          <el-button v-if="canQueryCourse" link type="primary" @click="goDetail(scope.row)">{{ scope.row.courseName }}</el-button>
          <span v-else>{{ scope.row.courseName }}</span>
        </template>
      </el-table-column>
      <el-table-column label="分类" prop="courseCategory" width="140" />
      <el-table-column label="负责人" prop="ownerName" width="110" />
      <el-table-column label="状态" prop="status" width="90" align="center">
        <template #default="scope">
          <el-tag :type="optionTagType(courseStatusOptions, scope.row.status)" effect="light">
            {{ optionLabel(courseStatusOptions, scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="模块" prop="moduleCount" width="80" align="center" />
      <el-table-column label="资料" width="130" align="center">
        <template #default="scope">
          {{ scope.row.parsedCount }} / {{ scope.row.documentCount }}
        </template>
      </el-table-column>
      <el-table-column label="学员" prop="studentCount" width="90" align="center" />
      <el-table-column label="当前知识库" width="130" align="center">
        <template #default="scope">
          <span>{{ scope.row.currentVersion || '-' }}</span>
          <el-tag v-if="scope.row.currentVersionStatus" size="small" type="success" class="ml6">
            {{ scope.row.currentVersionStatus }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" width="170" />
      <el-table-column label="操作" width="240" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button v-hasPermi="['course:course:query']" link type="primary" icon="View" @click="goDetail(scope.row)">详情</el-button>
          <el-button v-hasPermi="['course:course:edit']" link type="primary" icon="Edit" @click="openCourseDialog(scope.row)">编辑</el-button>
          <el-button v-hasPermi="['course:course:edit']" link type="primary" icon="Switch" @click="toggleCourseStatus(scope.row)">
            {{ scope.row.status === 'active' ? '停用' : '启用' }}
          </el-button>
          <el-button v-hasPermi="['course:course:remove']" link type="danger" icon="Delete" @click="removeCourses(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <el-dialog :title="courseForm.id ? '修改课程' : '新增课程'" v-model="courseDialogOpen" width="620px" append-to-body @closed="resetCourseForm">
      <el-form ref="courseFormRef" :model="courseForm" :rules="courseRules" label-width="96px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课程编码" prop="courseCode">
              <el-input v-model="courseForm.courseCode" maxlength="64" placeholder="请输入课程编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程名称" prop="courseName">
              <el-input v-model="courseForm.courseName" maxlength="200" placeholder="请输入课程名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课程分类" prop="courseCategory">
              <el-input v-model="courseForm.courseCategory" maxlength="100" placeholder="请输入课程分类" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开课日期" prop="startDate">
              <el-date-picker v-model="courseForm.startDate" type="date" value-format="YYYY-MM-DD" placeholder="请选择日期" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课程状态" prop="status">
              <el-select v-model="courseForm.status" style="width: 100%">
                <el-option v-for="item in courseStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序" prop="sortOrder">
              <el-input-number v-model="courseForm.sortOrder" :min="0" :max="9999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="学员下载" prop="allowDownload">
          <el-switch v-model="courseForm.allowDownload" />
          <span class="download-hint">仅允许下载当前已发布知识库版本中的资料</span>
        </el-form-item>
        <el-form-item label="课程简介" prop="description">
          <el-input v-model="courseForm.description" type="textarea" :rows="3" maxlength="1000" show-word-limit />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="courseForm.remark" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="savingCourse" @click="submitCourse">确 定</el-button>
        <el-button :disabled="savingCourse" @click="courseDialogOpen = false">取 消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="Course">
import { useRouter } from 'vue-router'
import { addCourse, delCourse, getCourse, listCourse, updateCourse } from '@/api/course'
import auth from '@/plugins/auth'
import type { Course, CourseQueryParams } from '@/types'
import {
  courseStatusOptions,
  optionLabel,
  optionTagType
} from './mock'

const { proxy } = getCurrentInstance()
const router = useRouter()

const loading = ref(false)
const showSearch = ref(true)
const ids = ref<number[]>([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)
const courseList = ref<Course[]>([])
const canQueryCourse = auth.hasPermi('course:course:query')
const courseDialogOpen = ref(false)
const savingCourse = ref(false)
const courseFormRef = ref()
const courseForm = reactive<Course>({
  courseCode: '',
  courseName: '',
  courseCategory: '',
  description: '',
  startDate: undefined,
  allowDownload: false,
  status: 'active',
  sortOrder: 0,
  remark: ''
})
const courseRules = {
  courseName: [{ required: true, message: '课程名称不能为空', trigger: 'blur' }]
}

const queryParams = reactive<CourseQueryParams>({
  pageNum: 1,
  pageSize: 10,
  courseName: '',
  courseCategory: '',
  status: ''
})

const activeCourseCount = computed(() => courseList.value.filter((item: Course) => item.status === 'active').length)
const documentTotal = computed(() => courseList.value.reduce(
  (sum: number, item: Course) => sum + (item.documentCount || 0), 0
))
const studentTotal = computed(() => courseList.value.reduce(
  (sum: number, item: Course) => sum + (item.studentCount || 0), 0
))

async function getList() {
  loading.value = true
  try {
    const response = await listCourse(queryParams)
    courseList.value = response.rows || []
    total.value = response.total || 0
  } finally {
    loading.value = false
  }
}

function handleQuery() {
  queryParams.pageNum = 1
  getList()
}

function resetQuery() {
  proxy?.resetForm('queryRef')
  handleQuery()
}

function handleSelectionChange(selection: Course[]) {
  ids.value = selection.map(item => item.id!)
  single.value = selection.length !== 1
  multiple.value = selection.length === 0
}

function goDetail(row: Course) {
  router.push(`/course/detail/${row.id}`)
}

function resetCourseForm() {
  Object.assign(courseForm, {
    id: undefined,
    courseCode: '',
    courseName: '',
    courseCategory: '',
    description: '',
    startDate: undefined,
    allowDownload: false,
    status: 'active',
    sortOrder: 0,
    remark: ''
  })
  courseFormRef.value?.clearValidate()
}

async function openCourseDialog(row?: Course) {
  resetCourseForm()
  if (row?.id) {
    const response = await getCourse(row.id)
    Object.assign(courseForm, response.data)
  }
  courseDialogOpen.value = true
}

function editSelectedCourse() {
  const row = courseList.value.find((item: Course) => item.id === ids.value[0])
  if (row) openCourseDialog(row)
}

async function submitCourse() {
  const valid = await courseFormRef.value?.validate().catch(() => false)
  if (!valid) return
  savingCourse.value = true
  const isEdit = Boolean(courseForm.id)
  try {
    const payload: Course = {
      ...courseForm,
      courseCode: courseForm.courseCode?.trim(),
      courseName: courseForm.courseName?.trim(),
      courseCategory: courseForm.courseCategory?.trim(),
      description: courseForm.description?.trim(),
      remark: courseForm.remark?.trim()
    }
    if (isEdit) {
      await updateCourse(payload)
    } else {
      await addCourse(payload)
    }
    courseDialogOpen.value = false
    await getList()
    proxy?.$modal.msgSuccess(isEdit ? '课程修改成功' : '课程新增成功')
  } finally {
    savingCourse.value = false
  }
}

async function removeCourses(row?: Course) {
  const targetIds = row?.id ? [row.id] : ids.value
  if (!targetIds.length) return
  const names = row?.courseName || courseList.value
    .filter((item: Course) => targetIds.includes(item.id!))
    .map((item: Course) => item.courseName)
    .join('、')
  try {
    await proxy?.$modal.confirm(`确认删除课程“${names}”吗？课程下存在模块或资料时将无法删除。`)
  } catch {
    return
  }
  await delCourse(targetIds)
  await getList()
  proxy?.$modal.msgSuccess('课程删除成功')
}

async function toggleCourseStatus(row: Course) {
  if (!row.id) return
  const status = row.status === 'active' ? 'disabled' : 'active'
  await updateCourse({ ...row, status })
  await getList()
  proxy?.$modal.msgSuccess(status === 'active' ? '课程已启用' : '课程已停用')
}

getList()
</script>

<style scoped lang="scss">
.course-page {
  .download-hint {
    margin-left: 10px;
    color: #909399;
    font-size: 12px;
  }

  .course-summary {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 12px;
  }

  .summary-item {
    min-height: 72px;
    padding: 14px 16px;
    border: 1px solid #e5e6eb;
    border-radius: 6px;
    background: #fff;
  }

  .summary-label {
    display: block;
    margin-bottom: 8px;
    color: #606266;
    font-size: 13px;
  }

  .summary-item strong {
    color: #1f2d3d;
    font-size: 24px;
    line-height: 1;
  }

  .ml6 {
    margin-left: 6px;
  }
}

@media (max-width: 960px) {
  .course-page .course-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
