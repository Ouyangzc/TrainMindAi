<template>
  <div class="app-container course-page">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="课程名称" prop="keyword">
        <el-input
          v-model="queryParams.keyword"
          placeholder="请输入课程名称或编码"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="课程分类" prop="category">
        <el-select v-model="queryParams.category" placeholder="课程分类" clearable style="width: 200px">
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
        <el-button type="primary" plain icon="Plus" @click="handleMockAction('新增课程')">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="Edit" :disabled="single" @click="handleMockAction('修改课程')">修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleMockAction('删除课程')">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="handleQuery" />
    </el-row>

    <div class="course-summary">
      <div class="summary-item">
        <span class="summary-label">课程总数</span>
        <strong>{{ courses.length }}</strong>
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

    <el-table v-loading="loading" :data="pagedList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="课程编码" prop="code" width="130" />
      <el-table-column label="课程名称" min-width="230" :show-overflow-tooltip="true">
        <template #default="scope">
          <el-button link type="primary" @click="goDetail(scope.row)">{{ scope.row.name }}</el-button>
        </template>
      </el-table-column>
      <el-table-column label="分类" prop="category" width="140" />
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
          <span>{{ scope.row.currentVersion }}</span>
          <el-tag size="small" type="success" class="ml6">{{ scope.row.currentVersionStatus }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" width="170" />
      <el-table-column label="操作" width="240" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="View" @click="goDetail(scope.row)">详情</el-button>
          <el-button link type="primary" icon="Edit" @click="handleMockAction('编辑课程')">编辑</el-button>
          <el-button link type="primary" icon="Switch" @click="handleMockAction('启停课程')">启停</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="filteredList.length > 0"
      :total="filteredList.length"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="handleQuery"
    />
  </div>
</template>

<script setup lang="ts" name="Course">
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  courses,
  courseStatusOptions,
  optionLabel,
  optionTagType,
  type CourseItem,
  type CourseStatus
} from './mock'

const { proxy } = getCurrentInstance()
const router = useRouter()

const loading = ref(false)
const showSearch = ref(true)
const ids = ref<number[]>([])
const single = ref(true)
const multiple = ref(true)

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  keyword: '',
  category: '',
  status: '' as CourseStatus | ''
})

const filteredList = computed(() => {
  const keyword = queryParams.keyword.trim().toLowerCase()
  return courses.filter(item => {
    const matchKeyword = !keyword || item.name.toLowerCase().includes(keyword) || item.code.toLowerCase().includes(keyword)
    const matchCategory = !queryParams.category || item.category === queryParams.category
    const matchStatus = !queryParams.status || item.status === queryParams.status
    return matchKeyword && matchCategory && matchStatus
  })
})

const pagedList = computed(() => {
  const start = (queryParams.pageNum - 1) * queryParams.pageSize
  return filteredList.value.slice(start, start + queryParams.pageSize)
})

const activeCourseCount = computed(() => courses.filter(item => item.status === 'active').length)
const documentTotal = computed(() => courses.reduce((sum, item) => sum + item.documentCount, 0))
const studentTotal = computed(() => courses.reduce((sum, item) => sum + item.studentCount, 0))

function handleQuery() {
  queryParams.pageNum = 1
}

function resetQuery() {
  proxy?.resetForm('queryRef')
  handleQuery()
}

function handleSelectionChange(selection: CourseItem[]) {
  ids.value = selection.map(item => item.id)
  single.value = selection.length !== 1
  multiple.value = selection.length === 0
}

function goDetail(row: CourseItem) {
  router.push(`/course/detail/${row.id}`)
}

function handleMockAction(name: string) {
  ElMessage.info(`${name}：页面效果阶段，待确认后接入后端`)
}
</script>

<style scoped lang="scss">
.course-page {
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
