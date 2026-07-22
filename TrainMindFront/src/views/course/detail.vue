<template>
  <div class="app-container course-detail">
    <div class="detail-header">
      <div>
        <div class="breadcrumb-line">
          <el-button link icon="ArrowLeft" @click="goBack">课程管理</el-button>
          <span>/</span>
          <span>{{ course?.courseCode }}</span>
        </div>
        <h2>{{ course?.courseName }}</h2>
        <div class="header-meta">
          <el-tag :type="optionTagType(courseStatusOptions, course?.status || '')">
            {{ optionLabel(courseStatusOptions, course?.status || '') }}
          </el-tag>
          <span>负责人：{{ course?.ownerName }}</span>
          <span>分类：{{ course?.courseCategory || '-' }}</span>
          <span>更新时间：{{ course?.updateTime }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button v-hasPermi="['course:course:edit']" icon="Edit" @click="openCourseEditDialog">编辑</el-button>
        <el-button v-if="canViewDocuments" v-hasPermi="['course:document:upload']" type="primary" icon="Upload" @click="activeTab = 'documents'">上传资料</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="course-tabs">
      <el-tab-pane label="基本信息" name="basic">
        <div class="basic-grid">
          <div class="info-panel">
            <div class="panel-title">课程信息</div>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="课程编码">{{ course?.courseCode }}</el-descriptions-item>
              <el-descriptions-item label="课程分类">{{ course?.courseCategory || '-' }}</el-descriptions-item>
              <el-descriptions-item label="主负责人">{{ course?.ownerName }}</el-descriptions-item>
              <el-descriptions-item label="开课日期">{{ course?.startDate }}</el-descriptions-item>
              <el-descriptions-item label="学员下载">{{ course?.allowDownload ? '允许' : '禁止' }}</el-descriptions-item>
              <el-descriptions-item label="课程状态">
                <el-tag :type="optionTagType(courseStatusOptions, course?.status || '')">
                  {{ optionLabel(courseStatusOptions, course?.status || '') }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="当前知识库">
                {{ course?.currentVersion || '-' }}
                <span v-if="course?.currentVersionStatus"> / {{ course.currentVersionStatus }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="备注" :span="2">{{ course?.remark }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="metric-panel">
            <div class="metric-item">
              <span>模块数</span>
              <strong>{{ course?.moduleCount || courseModules.length }}</strong>
            </div>
            <div class="metric-item">
              <span>资料数</span>
              <strong>{{ course?.documentCount || courseDocuments.length }}</strong>
            </div>
            <div class="metric-item">
              <span>已解析</span>
              <strong>{{ course?.parsedCount || parsedDocumentCount }}</strong>
            </div>
            <div class="metric-item">
              <span>成员数</span>
              <strong>{{ course?.studentCount || courseMembers.length }}</strong>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane v-if="canViewModules" label="模块管理" name="modules">
        <div class="tab-toolbar">
          <el-button v-hasPermi="['course:module:add']" type="primary" plain icon="Plus" @click="openModuleDialog()">新增模块</el-button>
          <el-button v-hasPermi="['course:module:edit']" icon="Sort" :loading="savingModuleSort" @click="saveModuleSort">保存排序</el-button>
        </div>
        <el-table :data="courseModules" row-key="id">
          <el-table-column label="排序" width="130" align="center">
            <template #default="scope">
              <el-input-number v-model="scope.row.sortOrder" :min="0" :max="9999" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="模块编码" prop="moduleCode" width="120" />
          <el-table-column label="模块名称" prop="moduleName" min-width="180" />
          <el-table-column label="资料数" width="90" align="center">
            <template #default="scope">{{ moduleDocumentCount(scope.row.id) }}</template>
          </el-table-column>
          <el-table-column label="状态" prop="status" width="90" align="center">
            <template #default="scope">
              <el-tag :type="optionTagType(moduleStatusOptions, scope.row.status)">
                {{ optionLabel(moduleStatusOptions, scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="备注" prop="remark" min-width="220" :show-overflow-tooltip="true" />
          <el-table-column label="操作" width="210" align="center" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button v-hasPermi="['course:module:edit']" link type="primary" icon="Edit" @click="openModuleDialog(scope.row)">编辑</el-button>
              <el-button
                v-hasPermi="['course:module:edit']"
                link
                type="primary"
                icon="Switch"
                :loading="updatingModuleIds.includes(scope.row.id)"
                @click="toggleModuleStatus(scope.row)"
              >{{ scope.row.status === 'active' ? '停用' : '启用' }}</el-button>
              <el-button
                v-hasPermi="['course:module:remove']"
                link
                type="danger"
                icon="Delete"
                :loading="deletingModuleIds.includes(scope.row.id)"
                @click="deleteModule(scope.row)"
              >删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="canViewDocuments" label="资料管理" name="documents">
        <div class="document-layout">
          <aside class="module-tree">
            <div class="tree-title">资料范围</div>
            <el-menu :default-active="selectedModuleKey" @select="selectedModuleKey = $event">
              <el-menu-item index="all">
                <el-icon><Folder /></el-icon>
                <span>全部资料</span>
              </el-menu-item>
              <el-menu-item index="public">
                <el-icon><Collection /></el-icon>
                <span>课程公共资料</span>
              </el-menu-item>
              <el-menu-item
                v-for="item in normalModules"
                :key="item.id"
                :index="String(item.id)"
              >
                <el-icon><Document /></el-icon>
                <span>{{ item.moduleCode }} {{ item.moduleName }}</span>
              </el-menu-item>
            </el-menu>
          </aside>

          <section class="document-main">
            <el-form :model="documentQuery" :inline="true" class="document-search">
              <el-form-item label="关键词">
                <el-input v-model="documentQuery.keyword" placeholder="资料名称或文件名" clearable style="width: 220px" />
              </el-form-item>
              <el-form-item label="文件类型">
                <el-select v-model="documentQuery.documentType" placeholder="全部" clearable style="width: 140px">
                  <el-option label="PDF" value="pdf" />
                  <el-option label="DOCX" value="docx" />
                  <el-option label="PPTX" value="pptx" />
                  <el-option label="XLSX" value="xlsx" />
                </el-select>
              </el-form-item>
              <el-form-item label="解析状态">
                <el-select v-model="documentQuery.versionStatus" placeholder="全部" clearable style="width: 150px">
                  <el-option
                    v-for="item in versionStatusOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" icon="Search">搜索</el-button>
                <el-button icon="Refresh" @click="resetDocumentQuery">重置</el-button>
              </el-form-item>
            </el-form>

            <div class="tab-toolbar compact">
              <el-button v-hasPermi="['course:document:upload']" type="primary" plain icon="Upload" @click="openUploadDialog('new')">上传资料</el-button>
              <el-button v-hasPermi="['course:document:download']" icon="Download" @click="handleMockAction('批量下载')">批量下载</el-button>
            </div>

            <el-table :data="filteredDocuments">
              <el-table-column label="资料名称" min-width="220" :show-overflow-tooltip="true">
                <template #default="scope">
                  <div class="document-title">
                    <el-tag size="small" effect="plain">{{ (scope.row.documentType || '-').toUpperCase() }}</el-tag>
                    <span>{{ scope.row.title }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="所属模块" width="150">
                <template #default="scope">{{ moduleName(scope.row.moduleId) }}</template>
              </el-table-column>
              <el-table-column label="版本" width="80" align="center">
                <template #default="scope">V{{ scope.row.versionNo || '-' }}</template>
              </el-table-column>
              <el-table-column label="解析状态" width="110" align="center">
                <template #default="scope">
                  <el-tooltip
                    v-if="scope.row.versionStatus === 'failed'"
                    :content="scope.row.parseErrorMessage"
                    placement="top"
                  >
                    <el-tag :type="optionTagType(versionStatusOptions, scope.row.versionStatus)">
                      {{ optionLabel(versionStatusOptions, scope.row.versionStatus) }}
                    </el-tag>
                  </el-tooltip>
                  <el-tag v-else :type="optionTagType(versionStatusOptions, scope.row.versionStatus)">
                    {{ optionLabel(versionStatusOptions, scope.row.versionStatus) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="大小" width="100">
                <template #default="scope">{{ formatFileSize(scope.row.fileSize) }}</template>
              </el-table-column>
              <el-table-column label="上传人" prop="createBy" width="110" />
              <el-table-column label="更新时间" prop="updateTime" width="170" />
              <el-table-column label="操作" width="330" align="center" class-name="small-padding fixed-width">
                <template #default="scope">
                  <el-button v-hasPermi="['course:document:upload']" link type="primary" icon="Upload" @click="openUploadDialog('version', scope.row)">新版本</el-button>
                  <el-button v-hasPermi="['course:document:query']" link type="primary" icon="Clock" @click="openVersionDialog(scope.row)">版本历史</el-button>
                  <el-button
                    v-hasPermi="['course:document:download']"
                    link
                    type="primary"
                    icon="Download"
                    :loading="downloadingVersionId === scope.row.latestVersionId"
                    @click="downloadLatestVersion(scope.row)"
                  >下载</el-button>
                  <el-button
                    v-hasPermi="['course:document:parse']"
                    link
                    type="primary"
                    icon="Cpu"
                    :loading="parsingVersionIds.includes(scope.row.latestVersionId)"
                    :disabled="scope.row.versionStatus === 'parsing'"
                    @click="startParse(scope.row)"
                  >{{ scope.row.versionStatus === 'failed' ? '重新解析' : '解析' }}</el-button>
                  <el-button
                    v-hasPermi="['course:document:remove']"
                    link
                    type="danger"
                    icon="Delete"
                    :loading="deletingDocumentIds.includes(scope.row.id)"
                    :disabled="scope.row.versionStatus === 'parsing'"
                    @click="deleteDocument(scope.row)"
                  >删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane v-if="canViewKnowledge" label="知识库治理" name="knowledge">
        <div v-loading="knowledgeLoading" class="knowledge-shell">
          <div class="knowledge-status">
            <div>
              <span class="muted">知识库名称</span>
              <strong>{{ knowledgeBase?.name || `${course?.courseName || ''}知识库` }}</strong>
            </div>
            <div>
              <span class="muted">当前发布版本</span>
              <strong>{{ publishedKnowledgeVersion ? `V${publishedKnowledgeVersion.versionNo}` : '-' }}</strong>
            </div>
            <div>
              <span class="muted">草稿状态</span>
              <el-tag :type="knowledgeStatusTag(activeKnowledgeVersion?.status)">
                {{ knowledgeStatusLabel(activeKnowledgeVersion?.status) }}
              </el-tag>
            </div>
            <el-button
              v-hasPermi="['course:knowledge-base:edit']"
              type="primary"
              :loading="creatingDraft"
              :disabled="Boolean(activeKnowledgeVersion)"
              @click="createKnowledgeDraft"
            >创建草稿</el-button>
          </div>
          <el-tabs v-model="knowledgeTab">
            <el-tab-pane label="草稿资料" name="draft">
              <template v-if="activeKnowledgeVersion">
                <div class="tab-toolbar">
                  <el-button
                    v-hasPermi="['course:knowledge-base:edit']"
                    type="primary"
                    :loading="savingSnapshot"
                    :disabled="activeKnowledgeVersion.status !== 'draft'"
                    @click="saveKnowledgeSnapshot"
                  >保存资料快照</el-button>
                  <el-button
                    v-hasPermi="['course:knowledge-base:build']"
                    type="success"
                    :loading="buildingKnowledge"
                    :disabled="!['draft', 'failed'].includes(activeKnowledgeVersion.status || '') || !selectedSnapshotIds.length"
                    @click="buildKnowledge"
                  >{{ activeKnowledgeVersion.status === 'failed' ? '重新构建' : '开始构建' }}</el-button>
                  <el-button
                    v-hasPermi="['course:knowledge-base:publish']"
                    type="primary"
                    :loading="publishingKnowledge"
                    :disabled="activeKnowledgeVersion.status !== 'ready'"
                    @click="publishKnowledge"
                  >发布版本</el-button>
                </div>
                <el-alert
                  v-if="activeKnowledgeVersion.buildErrorMessage"
                  :title="activeKnowledgeVersion.buildErrorMessage"
                  type="error"
                  show-icon
                  :closable="false"
                  class="knowledge-alert"
                />
                <el-table
                  ref="snapshotTableRef"
                  :data="snapshotCandidates"
                  row-key="documentVersionId"
                  @selection-change="handleSnapshotSelection"
                >
                  <el-table-column
                    type="selection"
                    width="48"
                    :selectable="() => canEditKnowledge && activeKnowledgeVersion?.status === 'draft'"
                  />
                  <el-table-column label="资料" prop="documentTitle" min-width="220" />
                  <el-table-column label="文件名" prop="originalFilename" min-width="220" />
                  <el-table-column label="版本" width="80" align="center">
                    <template #default="scope">V{{ scope.row.versionNo }}</template>
                  </el-table-column>
                  <el-table-column label="模块" width="160">
                    <template #default="scope">{{ moduleName(scope.row.moduleId ?? null) }}</template>
                  </el-table-column>
                </el-table>
              </template>
              <el-empty v-else description="暂无活动草稿，请先创建草稿版本" />
            </el-tab-pane>
            <el-tab-pane label="构建任务" name="tasks">
              <el-descriptions v-if="knowledgeBuildTask" :column="2" border>
                <el-descriptions-item label="任务编号">{{ knowledgeBuildTask.id }}</el-descriptions-item>
                <el-descriptions-item label="任务状态">{{ knowledgeBuildTask.status }}</el-descriptions-item>
                <el-descriptions-item label="当前步骤">{{ knowledgeBuildTask.currentStep || '-' }}</el-descriptions-item>
                <el-descriptions-item label="进度">
                  <el-progress :percentage="knowledgeBuildTask.progress || 0" />
                </el-descriptions-item>
                <el-descriptions-item v-if="knowledgeBuildTask.errorMessage" label="错误信息" :span="2">
                  {{ knowledgeBuildTask.errorMessage }}
                </el-descriptions-item>
              </el-descriptions>
              <el-empty v-else description="暂无构建任务" />
            </el-tab-pane>
            <el-tab-pane label="版本历史" name="versions">
              <el-table :data="knowledgeVersions">
                <el-table-column label="版本" width="90" align="center">
                  <template #default="scope">V{{ scope.row.versionNo }}</template>
                </el-table-column>
                <el-table-column label="状态" width="110" align="center">
                  <template #default="scope">
                    <el-tag :type="knowledgeStatusTag(scope.row.status)">
                      {{ knowledgeStatusLabel(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="分片数" prop="chunkCount" width="100" />
                <el-table-column label="发布时间" prop="publishedAt" width="180" />
                <el-table-column label="发布人" prop="publishedBy" width="120" />
                <el-table-column label="备注" prop="remark" min-width="180" />
                <el-table-column label="操作" width="100" align="center">
                  <template #default="scope">
                    <el-button
                      v-if="canPublishKnowledge && ['published', 'archived'].includes(scope.row.status)"
                      link
                      type="primary"
                      :disabled="Boolean(activeKnowledgeVersion)"
                      @click="rollbackKnowledge(scope.row)"
                    >回滚</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-tab-pane>

      <el-tab-pane v-if="canViewMembers" label="课程成员" name="members">
        <div class="tab-toolbar">
          <el-button v-hasPermi="['course:member:edit']" type="primary" plain icon="Plus" @click="openMemberDialog()">添加成员</el-button>
          <el-button v-hasPermi="['course:member:edit']" icon="Connection" @click="openOwnerTransferDialog">转移负责人</el-button>
        </div>
        <el-table v-loading="membersLoading" :data="courseMembers">
          <el-table-column label="用户名" prop="userName" width="140" />
          <el-table-column label="姓名" prop="nickName" width="140" />
          <el-table-column label="角色" prop="accessRole" width="100" align="center">
            <template #default="scope">
              <el-tag :type="optionTagType(memberRoleOptions, scope.row.accessRole)">
                {{ optionLabel(memberRoleOptions, scope.row.accessRole) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="accessStatus" width="100" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.accessStatus === 'active' ? 'success' : 'info'">
                {{ scope.row.accessStatus === 'active' ? '有效' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="生效时间" prop="startAt" width="170" />
          <el-table-column label="有效期至" prop="endAt" width="170" />
          <el-table-column label="操作" width="220" align="center" class-name="small-padding fixed-width">
            <template #default="scope">
              <template v-if="canEditMembers && scope.row.accessRole !== 'owner'">
                <el-button link type="primary" icon="Edit" @click="openMemberDialog(scope.row)">编辑</el-button>
                <el-button link type="primary" icon="Switch" @click="toggleMemberStatus(scope.row)">
                  {{ scope.row.accessStatus === 'active' ? '停用' : '启用' }}
                </el-button>
                <el-button link type="danger" icon="Delete" @click="removeMember(scope.row)">移除</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog :title="moduleDialogTitle" v-model="moduleDialogOpen" width="520px" append-to-body @closed="resetModuleForm">
      <el-form label-width="88px">
        <el-form-item label="模块编码">
          <el-input v-model="moduleForm.moduleCode" maxlength="64" placeholder="例如 M1" />
        </el-form-item>
        <el-form-item label="模块名称" required>
          <el-input v-model="moduleForm.moduleName" maxlength="200" placeholder="请输入模块名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="moduleForm.sortOrder" :min="0" :max="9999" controls-position="right" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="moduleForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模块说明">
          <el-input v-model="moduleForm.description" type="textarea" maxlength="1000" show-word-limit />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="moduleForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="savingModule" @click="submitModule">确 定</el-button>
        <el-button :disabled="savingModule" @click="moduleDialogOpen = false">取 消</el-button>
      </template>
    </el-dialog>

    <el-dialog :title="uploadTitle" v-model="uploadOpen" width="560px" append-to-body @closed="resetUploadForm">
      <el-form label-width="96px">
        <el-form-item v-if="uploadMode === 'new'" label="所属模块">
          <el-select v-model="uploadForm.moduleId" placeholder="请选择模块" style="width: 100%">
            <el-option label="课程公共资料" :value="0" />
            <el-option
              v-for="item in normalModules"
              :key="item.id"
              :label="`${item.moduleCode} ${item.moduleName}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="uploadMode === 'new'" label="资料标题">
          <el-input v-model="uploadForm.title" placeholder="请输入资料标题" />
        </el-form-item>
        <el-form-item v-else label="资料名称">
          <span>{{ uploadTarget?.title }}</span>
        </el-form-item>
        <el-form-item label="上传文件">
          <el-upload
            v-model:file-list="uploadFiles"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="handleUploadFileChange"
            :on-exceed="handleUploadExceed"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖入文件或点击选择</div>
            <template #tip>
              <div class="el-upload__tip">支持 pdf、docx、pptx、xlsx，单文件最大 200MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" v-model="uploadForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" :loading="uploading" @click="submitUpload">确 定</el-button>
          <el-button :disabled="uploading" @click="uploadOpen = false">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog title="版本历史" v-model="versionOpen" width="720px" append-to-body>
      <el-table v-loading="versionLoading" :data="versionRows">
        <el-table-column label="版本" prop="versionNo" width="80" align="center" />
        <el-table-column label="文件名" prop="filename" min-width="220" />
        <el-table-column label="状态" prop="status" width="110" align="center">
          <template #default="scope">
            <el-tag :type="optionTagType(versionStatusOptions, scope.row.status)">
              {{ optionLabel(versionStatusOptions, scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" prop="fileSize" width="100" />
        <el-table-column label="上传时间" prop="updateTime" width="170" />
        <el-table-column label="操作" width="90" align="center">
          <template #default="scope">
            <el-button
              v-hasPermi="['course:document:download']"
              link
              type="primary"
              icon="Download"
              :loading="downloadingVersionId === scope.row.id"
              @click="downloadHistoryVersion(scope.row)"
            >下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog :title="memberForm.id ? '编辑成员' : '添加成员'" v-model="memberDialogOpen" width="520px" append-to-body>
      <el-form label-width="90px">
        <el-form-item label="系统用户" required>
          <el-select
            v-model="memberForm.userId"
            filterable
            remote
            :remote-method="searchUsers"
            :loading="userSearching"
            :disabled="Boolean(memberForm.id)"
            placeholder="输入用户名或姓名搜索"
            style="width: 100%"
          >
            <el-option
              v-for="item in userOptions"
              :key="item.userId"
              :label="`${item.nickName || item.userName}（${item.userName}）`"
              :value="item.userId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="课程角色">
          <el-radio-group v-model="memberForm.accessRole">
            <el-radio value="teacher">教师</el-radio>
            <el-radio value="student">学员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="授权状态">
          <el-radio-group v-model="memberForm.accessStatus">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="生效时间">
          <el-date-picker v-model="memberForm.startAt" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="有效期至">
          <el-date-picker v-model="memberForm.endAt" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="savingMember" @click="submitMember">确 定</el-button>
        <el-button @click="memberDialogOpen = false">取 消</el-button>
      </template>
    </el-dialog>

    <el-dialog title="转移课程负责人" v-model="ownerTransferOpen" width="480px" append-to-body>
      <el-alert title="转移后，原负责人将自动变更为教师。" type="warning" show-icon :closable="false" />
      <el-select v-model="ownerTargetUserId" placeholder="请选择当前课程成员" style="width: 100%; margin-top: 16px">
        <el-option
          v-for="item in transferableMembers"
          :key="item.userId"
          :label="`${item.nickName || item.userName}（${optionLabel(memberRoleOptions, item.accessRole)}）`"
          :value="item.userId"
        />
      </el-select>
      <template #footer>
        <el-button type="primary" :loading="transferringOwner" @click="submitOwnerTransfer">确认转移</el-button>
        <el-button @click="ownerTransferOpen = false">取 消</el-button>
      </template>
    </el-dialog>

    <el-dialog title="编辑课程" v-model="courseEditOpen" width="620px" append-to-body>
      <el-form ref="courseEditFormRef" :model="courseEditForm" :rules="courseEditRules" label-width="96px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课程编码" prop="courseCode">
              <el-input v-model="courseEditForm.courseCode" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程名称" prop="courseName">
              <el-input v-model="courseEditForm.courseName" maxlength="200" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课程分类">
              <el-input v-model="courseEditForm.courseCategory" maxlength="100" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开课日期">
              <el-date-picker v-model="courseEditForm.startDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="课程状态">
              <el-select v-model="courseEditForm.status" style="width: 100%">
                <el-option v-for="item in courseStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="courseEditForm.sortOrder" :min="0" :max="9999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="学员下载">
          <el-switch v-model="courseEditForm.allowDownload" />
          <span class="download-hint">仅允许下载当前已发布知识库版本中的资料</span>
        </el-form-item>
        <el-form-item label="课程简介">
          <el-input v-model="courseEditForm.description" type="textarea" :rows="3" maxlength="1000" show-word-limit />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="courseEditForm.remark" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="savingCourseEdit" @click="submitCourseEdit">确 定</el-button>
        <el-button :disabled="savingCourseEdit" @click="courseEditOpen = false">取 消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="CourseDetail">
import { useRoute, useRouter } from 'vue-router'
import { Collection, Document, Folder, UploadFilled } from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'
import { listUser } from '@/api/system/user'
import auth from '@/plugins/auth'
import {
  addCourseMember,
  addCourseModule,
  buildKnowledgeBaseVersion,
  createKnowledgeBaseDraft,
  delCourseMember,
  delCourseDocument,
  delCourseModule,
  downloadCourseDocumentVersion,
  getCourse,
  getCourseDocumentParseTask,
  getKnowledgeBase,
  getKnowledgeBaseBuildStatus,
  getKnowledgeBaseSnapshot,
  listCourseMember,
  listCourseDocument,
  listCourseDocumentVersion,
  listCourseModule,
  listKnowledgeBaseVersion,
  parseCourseDocumentVersion,
  publishKnowledgeBaseVersion,
  rollbackKnowledgeBaseVersion,
  saveKnowledgeBaseSnapshot,
  transferCourseOwner,
  uploadCourseDocument,
  uploadCourseDocumentVersion,
  updateCourseMember,
  updateCourse,
  updateCourseModule
} from '@/api/course'
import type {
  Course,
  CourseDocument,
  CourseDocumentVersion,
  CourseMember,
  CourseModule,
  KnowledgeBase,
  KnowledgeBaseBuildTask,
  KnowledgeBaseVersion,
  KnowledgeBaseVersionDocument,
  SysUser,
  VersionStatus
} from '@/types'
import {
  courseStatusOptions,
  moduleStatusOptions,
  versionStatusOptions,
  memberRoleOptions,
  optionLabel,
  optionTagType
} from './mock'

const route = useRoute()
const router = useRouter()
const { proxy } = getCurrentInstance()!
interface LocalUploadFile {
  name: string
  raw?: File
}

const courseId = computed(() => Number(route.params.courseId || 1001))
const canViewModules = auth.hasPermi('course:module:list')
const canViewDocuments = auth.hasPermi('course:document:list')
const canViewKnowledge = auth.hasPermi('course:knowledge-base:query')
const canEditKnowledge = auth.hasPermi('course:knowledge-base:edit')
const canPublishKnowledge = auth.hasPermi('course:knowledge-base:publish')
const canViewMembers = auth.hasPermi('course:member:list')
const canEditMembers = auth.hasPermi('course:member:edit')
const course = ref<Course>()
const activeTab = ref('basic')
const selectedModuleKey = ref('all')
const uploadOpen = ref(false)
const uploadTitle = ref('上传资料')
const uploadMode = ref<'new' | 'version'>('new')
const uploadTarget = ref<CourseDocument | null>(null)
const uploading = ref(false)
const uploadFiles = ref<LocalUploadFile[]>([])
const downloadingVersionId = ref<number | null>(null)
const parsingVersionIds = ref<number[]>([])
const deletingDocumentIds = ref<number[]>([])
const moduleDialogOpen = ref(false)
const moduleDialogTitle = ref('新增模块')
const savingModule = ref(false)
const savingModuleSort = ref(false)
const updatingModuleIds = ref<number[]>([])
const deletingModuleIds = ref<number[]>([])
const parsePollTimers = new Map<number, ReturnType<typeof setTimeout>>()
const versionOpen = ref(false)
const versionLoading = ref(false)
const currentDocument = ref<CourseDocument | null>(null)
const courseModules = ref<CourseModule[]>([])
const courseDocuments = ref<CourseDocument[]>([])
const knowledgeBase = ref<KnowledgeBase>()
const knowledgeVersions = ref<KnowledgeBaseVersion[]>([])
const knowledgeSnapshot = ref<KnowledgeBaseVersionDocument[]>([])
const selectedSnapshotIds = ref<number[]>([])
const knowledgeBuildTask = ref<KnowledgeBaseBuildTask>()
const knowledgeLoading = ref(false)
const creatingDraft = ref(false)
const savingSnapshot = ref(false)
const buildingKnowledge = ref(false)
const publishingKnowledge = ref(false)
const knowledgeTab = ref('draft')
const snapshotTableRef = ref()
const buildPollTimers = new Map<number, ReturnType<typeof setTimeout>>()
const courseMembers = ref<CourseMember[]>([])
const membersLoading = ref(false)
const memberDialogOpen = ref(false)
const savingMember = ref(false)
const userSearching = ref(false)
const userOptions = ref<SysUser[]>([])
const ownerTransferOpen = ref(false)
const ownerTargetUserId = ref<number>()
const transferringOwner = ref(false)
const courseEditOpen = ref(false)
const savingCourseEdit = ref(false)
const courseEditFormRef = ref()
const versionRows = ref<Array<{
  id: number
  versionNo: string
  filename: string
  status: VersionStatus
  fileSize: string
  updateTime?: string
}>>([])

const documentQuery = reactive({
  keyword: '',
  documentType: '',
  versionStatus: '' as VersionStatus | ''
})

const uploadForm = reactive({
  moduleId: 0,
  title: '',
  remark: ''
})
const moduleForm = reactive<CourseModule>({
  moduleCode: '',
  moduleName: '',
  description: '',
  sortOrder: 0,
  status: 'active',
  remark: ''
})
const memberForm = reactive<CourseMember>({
  userId: undefined,
  accessRole: 'student',
  accessStatus: 'active',
  startAt: undefined,
  endAt: undefined
})
const courseEditForm = reactive<Course>({})
const courseEditRules = {
  courseName: [{ required: true, message: '课程名称不能为空', trigger: 'blur' }]
}

const normalModules = computed(() => courseModules.value)
const parsedDocumentCount = computed(() => courseDocuments.value.filter((item: CourseDocument) => item.versionStatus === 'parsed').length)
const activeKnowledgeVersion = computed(() =>
  knowledgeVersions.value.find((item: KnowledgeBaseVersion) => ['draft', 'building', 'ready', 'failed'].includes(item.status || ''))
)
const publishedKnowledgeVersion = computed(() =>
  knowledgeVersions.value.find((item: KnowledgeBaseVersion) => item.id === knowledgeBase.value?.currentVersionId)
)
const transferableMembers = computed(() =>
  courseMembers.value.filter((item: CourseMember) => item.accessRole !== 'owner' && item.accessStatus === 'active')
)
const snapshotCandidates = computed<KnowledgeBaseVersionDocument[]>(() => {
  const rows = new Map<number, KnowledgeBaseVersionDocument>()
  knowledgeSnapshot.value.forEach((item: KnowledgeBaseVersionDocument) => {
    if (item.documentVersionId) rows.set(item.documentVersionId, item)
  })
  courseDocuments.value
    .filter((item: CourseDocument) => item.versionStatus === 'parsed' && item.latestVersionId)
    .forEach((item: CourseDocument) => {
    if (!rows.has(item.latestVersionId!)) {
      rows.set(item.latestVersionId!, {
        documentId: item.id,
        documentVersionId: item.latestVersionId,
        documentTitle: item.title,
        versionNo: item.versionNo,
        originalFilename: item.originalFilename,
        fileExt: item.fileExt,
        versionStatus: item.versionStatus,
        moduleId: item.moduleId
      })
    }
    })
  return [...rows.values()]
})

const filteredDocuments = computed(() => {
  const keyword = documentQuery.keyword.trim().toLowerCase()
  return courseDocuments.value.filter((item: CourseDocument) => {
    const matchModule =
      selectedModuleKey.value === 'all' ||
      (selectedModuleKey.value === 'public' && item.moduleId === null) ||
      String(item.moduleId) === selectedModuleKey.value
    const matchKeyword =
      !keyword ||
      (item.title || '').toLowerCase().includes(keyword) ||
      (item.originalFilename || '').toLowerCase().includes(keyword)
    const matchType = !documentQuery.documentType || item.documentType === documentQuery.documentType
    const matchStatus = !documentQuery.versionStatus || item.versionStatus === documentQuery.versionStatus
    return matchModule && matchKeyword && matchType && matchStatus
  })
})

function moduleName(moduleId: number | null) {
  if (moduleId === null) {
    return '课程公共资料'
  }
  const item = courseModules.value.find((module: CourseModule) => module.id === moduleId)
  return item ? `${item.moduleCode} ${item.moduleName}` : '-'
}

function moduleDocumentCount(moduleId?: number) {
  return courseDocuments.value.filter((item: CourseDocument) => item.moduleId === moduleId).length
}

function formatFileSize(size?: number) {
  if (!size) {
    return '-'
  }
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} KB`
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function loadDetail() {
  getCourse(courseId.value).then(response => {
    course.value = response.data
  })
  if (canViewModules) {
    listCourseModule(courseId.value).then(response => {
      courseModules.value = response.data || []
    })
  }
  if (canViewDocuments) {
    listCourseDocument(courseId.value).then(response => {
      courseDocuments.value = response.data || []
      courseDocuments.value.forEach((item: CourseDocument) => {
        if (item.versionStatus === 'parsing' && item.id && item.latestVersionId) {
          if (!parsingVersionIds.value.includes(item.latestVersionId)) {
            parsingVersionIds.value.push(item.latestVersionId)
          }
          pollParseTask(item.id, item.latestVersionId)
        }
      })
    })
  }
  if (canViewKnowledge) {
    loadKnowledge()
  }
  if (canViewMembers) {
    loadMembers()
  }
}

function resetDocumentQuery() {
  documentQuery.keyword = ''
  documentQuery.documentType = ''
  documentQuery.versionStatus = ''
}

async function refreshModules() {
  const response = await listCourseModule(courseId.value)
  courseModules.value = response.data || []
}

function openModuleDialog(row?: CourseModule) {
  if (row) {
    Object.assign(moduleForm, {
      id: row.id,
      moduleCode: row.moduleCode || '',
      moduleName: row.moduleName || '',
      description: row.description || '',
      sortOrder: row.sortOrder || 0,
      status: row.status || 'active',
      remark: row.remark || ''
    })
    moduleDialogTitle.value = '编辑模块'
  } else {
    moduleForm.sortOrder = courseModules.value.length
    moduleDialogTitle.value = '新增模块'
  }
  moduleDialogOpen.value = true
}

function resetModuleForm() {
  Object.assign(moduleForm, {
    id: undefined,
    moduleCode: '',
    moduleName: '',
    description: '',
    sortOrder: 0,
    status: 'active',
    remark: ''
  })
}

async function submitModule() {
  if (!moduleForm.moduleName?.trim()) {
    proxy?.$modal.msgWarning('请输入模块名称')
    return
  }
  const data: CourseModule = {
    moduleCode: moduleForm.moduleCode?.trim(),
    moduleName: moduleForm.moduleName.trim(),
    description: moduleForm.description?.trim(),
    sortOrder: moduleForm.sortOrder,
    status: moduleForm.status,
    remark: moduleForm.remark?.trim()
  }
  savingModule.value = true
  const isEdit = Boolean(moduleForm.id)
  try {
    if (moduleForm.id) {
      await updateCourseModule(courseId.value, moduleForm.id, data)
    } else {
      await addCourseModule(courseId.value, data)
    }
    moduleDialogOpen.value = false
    await refreshModules()
    proxy?.$modal.msgSuccess(isEdit ? '修改成功' : '新增成功')
  } finally {
    savingModule.value = false
  }
}

async function toggleModuleStatus(row: CourseModule) {
  if (!row.id) return
  updatingModuleIds.value.push(row.id)
  try {
    const status = row.status === 'active' ? 'disabled' : 'active'
    await updateCourseModule(courseId.value, row.id, { ...row, status })
    row.status = status
    proxy?.$modal.msgSuccess(status === 'active' ? '模块已启用' : '模块已停用')
  } finally {
    updatingModuleIds.value = updatingModuleIds.value.filter((id: number) => id !== row.id)
  }
}

async function saveModuleSort() {
  savingModuleSort.value = true
  try {
    await Promise.all(courseModules.value.map((item: CourseModule) =>
      updateCourseModule(courseId.value, item.id!, { ...item, sortOrder: item.sortOrder || 0 })
    ))
    await refreshModules()
    proxy?.$modal.msgSuccess('排序保存成功')
  } finally {
    savingModuleSort.value = false
  }
}

async function deleteModule(row: CourseModule) {
  if (!row.id) return
  if (moduleDocumentCount(row.id) > 0) {
    proxy?.$modal.msgWarning('该模块下仍有资料，不能删除')
    return
  }
  try {
    await proxy?.$modal.confirm(`确认删除模块“${row.moduleName}”吗？`)
  } catch {
    return
  }
  deletingModuleIds.value.push(row.id)
  try {
    await delCourseModule(courseId.value, row.id)
    await refreshModules()
    proxy?.$modal.msgSuccess('删除成功')
  } finally {
    deletingModuleIds.value = deletingModuleIds.value.filter((id: number) => id !== row.id)
  }
}

function openUploadDialog(mode: 'new' | 'version', document?: CourseDocument) {
  uploadMode.value = mode
  uploadTarget.value = document || null
  uploadTitle.value = mode === 'new' ? '上传资料' : '上传新版本'
  uploadOpen.value = true
}

function handleUploadFileChange(file: LocalUploadFile, files: LocalUploadFile[]) {
  uploadFiles.value = files
  if (!uploadForm.title && file.name) {
    uploadForm.title = file.name.replace(/\.[^.]+$/, '')
  }
}

function handleUploadExceed() {
  proxy?.$modal.msgWarning('每次只能上传一个文件')
}

function resetUploadForm() {
  uploadForm.moduleId = 0
  uploadForm.title = ''
  uploadForm.remark = ''
  uploadFiles.value = []
  uploadMode.value = 'new'
  uploadTarget.value = null
}

async function submitUpload() {
  const title = uploadForm.title.trim()
  if (uploadMode.value === 'new' && !title) {
    proxy?.$modal.msgWarning('请输入资料标题')
    return
  }
  if (uploadMode.value === 'version' && !uploadTarget.value?.id) {
    proxy?.$modal.msgError('未找到要更新的资料')
    return
  }

  const rawFile = uploadFiles.value[0]?.raw
  if (!rawFile) {
    proxy?.$modal.msgWarning('请选择上传文件')
    return
  }

  const extension = rawFile.name.split('.').pop()?.toLowerCase()
  if (!extension || !['pdf', 'docx', 'pptx', 'xlsx'].includes(extension)) {
    proxy?.$modal.msgWarning('仅支持 pdf、docx、pptx、xlsx 文件')
    return
  }
  if (rawFile.size > 200 * 1024 * 1024) {
    proxy?.$modal.msgWarning('文件大小不能超过 200MB')
    return
  }

  const data = new FormData()
  if (uploadForm.remark.trim()) {
    data.append('remark', uploadForm.remark.trim())
  }
  data.append('file', rawFile)

  uploading.value = true
  try {
    if (uploadMode.value === 'new') {
      if (uploadForm.moduleId) {
        data.append('moduleId', String(uploadForm.moduleId))
      }
      data.append('title', title)
      await uploadCourseDocument(courseId.value, data)
    } else {
      await uploadCourseDocumentVersion(courseId.value, uploadTarget.value!.id!, data)
    }
    proxy?.$modal.msgSuccess(uploadMode.value === 'new' ? '上传成功' : '新版本上传成功')
    uploadOpen.value = false
    const response = await listCourseDocument(courseId.value)
    courseDocuments.value = response.data || []
  } finally {
    uploading.value = false
  }
}

function openVersionDialog(row: CourseDocument) {
  currentDocument.value = row
  versionOpen.value = true
  versionLoading.value = true
  listCourseDocumentVersion(courseId.value, row.id!).then(response => {
    versionRows.value = (response.data || []).map((item: CourseDocumentVersion) => ({
      id: item.id!,
      versionNo: `V${item.versionNo || '-'}`,
      filename: item.originalFilename || '-',
      status: item.status || 'uploaded',
      fileSize: formatFileSize(item.fileSize),
      updateTime: item.createTime
    }))
  }).finally(() => {
    versionLoading.value = false
  })
}

async function downloadVersion(documentId: number, versionId: number, filename: string) {
  downloadingVersionId.value = versionId
  try {
    const data = await downloadCourseDocumentVersion(courseId.value, documentId, versionId)
    saveAs(data, filename)
  } finally {
    downloadingVersionId.value = null
  }
}

function downloadLatestVersion(row: CourseDocument) {
  if (!row.id || !row.latestVersionId) {
    proxy?.$modal.msgError('未找到可下载的资料版本')
    return
  }
  downloadVersion(row.id, row.latestVersionId, row.originalFilename || row.title || '课程资料')
}

function downloadHistoryVersion(row: { id: number; filename: string }) {
  if (!currentDocument.value?.id) {
    proxy?.$modal.msgError('未找到所属资料')
    return
  }
  downloadVersion(currentDocument.value.id, row.id, row.filename)
}

async function refreshDocuments() {
  const response = await listCourseDocument(courseId.value)
  courseDocuments.value = response.data || []
}

function stopParsePolling(versionId: number) {
  const timer = parsePollTimers.get(versionId)
  if (timer) {
    clearTimeout(timer)
    parsePollTimers.delete(versionId)
  }
  parsingVersionIds.value = parsingVersionIds.value.filter((id: number) => id !== versionId)
}

async function pollParseTask(documentId: number, versionId: number) {
  try {
    const response = await getCourseDocumentParseTask(courseId.value, documentId, versionId)
    const task = response.data
    if (task?.status === 'success') {
      stopParsePolling(versionId)
      await refreshDocuments()
      proxy?.$modal.msgSuccess('资料解析成功')
      return
    }
    if (task?.status === 'failed' || task?.status === 'cancelled') {
      stopParsePolling(versionId)
      await refreshDocuments()
      proxy?.$modal.msgError(task.errorMessage || (task.status === 'failed' ? '资料解析失败' : '解析任务已取消'))
      return
    }
    parsePollTimers.set(versionId, setTimeout(() => pollParseTask(documentId, versionId), 2000))
  } catch {
    stopParsePolling(versionId)
    await refreshDocuments()
  }
}

async function startParse(row: CourseDocument) {
  if (!row.id || !row.latestVersionId) {
    proxy?.$modal.msgError('未找到可解析的资料版本')
    return
  }
  if (parsingVersionIds.value.includes(row.latestVersionId)) {
    return
  }

  parsingVersionIds.value.push(row.latestVersionId)
  try {
    await parseCourseDocumentVersion(courseId.value, row.id, row.latestVersionId)
    row.versionStatus = 'parsing'
    proxy?.$modal.msgSuccess('解析任务已提交')
    pollParseTask(row.id, row.latestVersionId)
  } catch {
    stopParsePolling(row.latestVersionId)
  }
}

async function deleteDocument(row: CourseDocument) {
  if (!row.id) {
    proxy?.$modal.msgError('未找到要删除的资料')
    return
  }
  try {
    await proxy?.$modal.confirm(`确认删除资料“${row.title || row.originalFilename}”及其全部版本吗？`)
  } catch {
    return
  }

  deletingDocumentIds.value.push(row.id)
  try {
    await delCourseDocument(courseId.value, row.id)
    if (row.latestVersionId) {
      stopParsePolling(row.latestVersionId)
    }
    await refreshDocuments()
    proxy?.$modal.msgSuccess('删除成功')
  } finally {
    deletingDocumentIds.value = deletingDocumentIds.value.filter((id: number) => id !== row.id)
  }
}

function knowledgeStatusLabel(status?: string) {
  return ({
    draft: '草稿',
    building: '构建中',
    ready: '待发布',
    published: '已发布',
    archived: '已归档',
    failed: '构建失败'
  } as Record<string, string>)[status || ''] || '无活动版本'
}

function knowledgeStatusTag(status?: string) {
  return ({
    draft: 'info',
    building: 'warning',
    ready: 'success',
    published: 'success',
    archived: 'info',
    failed: 'danger'
  } as Record<string, 'success' | 'warning' | 'info' | 'danger'>)[status || ''] || 'info'
}

async function loadKnowledge() {
  knowledgeLoading.value = true
  try {
    const [baseResponse, versionsResponse] = await Promise.all([
      getKnowledgeBase(courseId.value),
      listKnowledgeBaseVersion(courseId.value)
    ])
    knowledgeBase.value = baseResponse.data
    knowledgeVersions.value = versionsResponse.data || []
    const active = activeKnowledgeVersion.value
    if (active?.id) {
      await loadKnowledgeSnapshot(active.id)
      if (active.status === 'building') {
        pollKnowledgeBuild(active.id)
      }
    } else {
      knowledgeSnapshot.value = []
      selectedSnapshotIds.value = []
    }
  } finally {
    knowledgeLoading.value = false
  }
}

async function loadKnowledgeSnapshot(versionId: number) {
  const response = await getKnowledgeBaseSnapshot(courseId.value, versionId)
  knowledgeSnapshot.value = response.data || []
  selectedSnapshotIds.value = knowledgeSnapshot.value
    .map((item: KnowledgeBaseVersionDocument) => item.documentVersionId)
    .filter((id: number | undefined): id is number => Boolean(id))
  await nextTick()
  snapshotTableRef.value?.clearSelection()
  snapshotCandidates.value.forEach((item: KnowledgeBaseVersionDocument) => {
    if (item.documentVersionId && selectedSnapshotIds.value.includes(item.documentVersionId)) {
      snapshotTableRef.value?.toggleRowSelection(item, true)
    }
  })
}

function handleSnapshotSelection(rows: KnowledgeBaseVersionDocument[]) {
  selectedSnapshotIds.value = rows
    .map(item => item.documentVersionId)
    .filter((id): id is number => Boolean(id))
}

async function createKnowledgeDraft() {
  creatingDraft.value = true
  try {
    await createKnowledgeBaseDraft(courseId.value)
    await loadKnowledge()
    proxy?.$modal.msgSuccess('草稿创建成功')
  } finally {
    creatingDraft.value = false
  }
}

async function saveKnowledgeSnapshot() {
  const versionId = activeKnowledgeVersion.value?.id
  if (!versionId) return
  savingSnapshot.value = true
  try {
    await saveKnowledgeBaseSnapshot(courseId.value, versionId, selectedSnapshotIds.value)
    await loadKnowledgeSnapshot(versionId)
    proxy?.$modal.msgSuccess('资料快照已保存')
  } finally {
    savingSnapshot.value = false
  }
}

function stopKnowledgeBuildPolling(versionId: number) {
  const timer = buildPollTimers.get(versionId)
  if (timer) clearTimeout(timer)
  buildPollTimers.delete(versionId)
}

async function pollKnowledgeBuild(versionId: number) {
  stopKnowledgeBuildPolling(versionId)
  try {
    const response = await getKnowledgeBaseBuildStatus(courseId.value, versionId)
    knowledgeBuildTask.value = response.data
    if (response.data?.status === 'success') {
      await loadKnowledge()
      proxy?.$modal.msgSuccess('知识库构建完成，可以发布')
      return
    }
    if (['failed', 'cancelled'].includes(response.data?.status || '')) {
      await loadKnowledge()
      proxy?.$modal.msgError(response.data?.errorMessage || '知识库构建失败')
      return
    }
    buildPollTimers.set(versionId, setTimeout(() => pollKnowledgeBuild(versionId), 2000))
  } catch {
    stopKnowledgeBuildPolling(versionId)
  }
}

async function buildKnowledge() {
  const versionId = activeKnowledgeVersion.value?.id
  if (!versionId) return
  buildingKnowledge.value = true
  try {
    const response = await buildKnowledgeBaseVersion(courseId.value, versionId)
    knowledgeBuildTask.value = response.data
    knowledgeTab.value = 'tasks'
    await loadKnowledge()
    pollKnowledgeBuild(versionId)
    proxy?.$modal.msgSuccess('构建任务已提交')
  } finally {
    buildingKnowledge.value = false
  }
}

async function publishKnowledge() {
  const versionId = activeKnowledgeVersion.value?.id
  if (!versionId) return
  try {
    await proxy?.$modal.confirm(`确认发布知识库 V${activeKnowledgeVersion.value?.versionNo} 吗？`)
  } catch {
    return
  }
  publishingKnowledge.value = true
  try {
    await publishKnowledgeBaseVersion(courseId.value, versionId)
    await Promise.all([loadKnowledge(), getCourse(courseId.value).then(response => { course.value = response.data })])
    proxy?.$modal.msgSuccess('知识库发布成功')
  } finally {
    publishingKnowledge.value = false
  }
}

async function rollbackKnowledge(row: KnowledgeBaseVersion) {
  if (!row.id) return
  try {
    await proxy?.$modal.confirm(`确认基于 V${row.versionNo} 创建回滚草稿吗？`)
  } catch {
    return
  }
  await rollbackKnowledgeBaseVersion(courseId.value, row.id)
  knowledgeTab.value = 'draft'
  await loadKnowledge()
  proxy?.$modal.msgSuccess('回滚草稿已创建，请重新构建后发布')
}

async function loadMembers() {
  membersLoading.value = true
  try {
    const response = await listCourseMember(courseId.value)
    courseMembers.value = response.data || []
  } finally {
    membersLoading.value = false
  }
}

async function searchUsers(keyword: string) {
  if (!keyword.trim()) {
    userOptions.value = []
    return
  }
  userSearching.value = true
  try {
    const response = await listUser({ pageNum: 1, pageSize: 20, userName: keyword.trim() })
    userOptions.value = response.rows || []
  } finally {
    userSearching.value = false
  }
}

function resetMemberForm() {
  Object.assign(memberForm, {
    id: undefined,
    userId: undefined,
    accessRole: 'student',
    accessStatus: 'active',
    startAt: undefined,
    endAt: undefined
  })
  userOptions.value = []
}

function openMemberDialog(row?: CourseMember) {
  resetMemberForm()
  if (row) {
    Object.assign(memberForm, row)
    userOptions.value = [{
      userId: row.userId,
      userName: row.userName,
      nickName: row.nickName
    }]
  }
  memberDialogOpen.value = true
}

async function submitMember() {
  if (!memberForm.userId) {
    proxy?.$modal.msgWarning('请选择系统用户')
    return
  }
  if (memberForm.startAt && memberForm.endAt && memberForm.startAt >= memberForm.endAt) {
    proxy?.$modal.msgWarning('有效期截止时间必须晚于生效时间')
    return
  }
  savingMember.value = true
  try {
    const payload: CourseMember = {
      userId: memberForm.userId,
      accessRole: memberForm.accessRole,
      accessStatus: memberForm.accessStatus,
      startAt: memberForm.startAt || undefined,
      endAt: memberForm.endAt || undefined
    }
    if (memberForm.id) {
      await updateCourseMember(courseId.value, memberForm.id, payload)
    } else {
      await addCourseMember(courseId.value, payload)
    }
    memberDialogOpen.value = false
    await loadMembers()
    proxy?.$modal.msgSuccess(memberForm.id ? '成员修改成功' : '成员添加成功')
    resetMemberForm()
  } finally {
    savingMember.value = false
  }
}

async function toggleMemberStatus(row: CourseMember) {
  if (!row.id) return
  await updateCourseMember(courseId.value, row.id, {
    ...row,
    accessStatus: row.accessStatus === 'active' ? 'disabled' : 'active'
  })
  await loadMembers()
  proxy?.$modal.msgSuccess('成员状态已更新')
}

async function removeMember(row: CourseMember) {
  if (!row.id) return
  try {
    await proxy?.$modal.confirm(`确认移除成员“${row.nickName || row.userName}”吗？`)
  } catch {
    return
  }
  await delCourseMember(courseId.value, row.id)
  await loadMembers()
  proxy?.$modal.msgSuccess('成员已移除')
}

function openOwnerTransferDialog() {
  ownerTargetUserId.value = undefined
  ownerTransferOpen.value = true
}

async function submitOwnerTransfer() {
  if (!ownerTargetUserId.value) {
    proxy?.$modal.msgWarning('请选择新负责人')
    return
  }
  transferringOwner.value = true
  try {
    await transferCourseOwner(courseId.value, ownerTargetUserId.value)
    ownerTransferOpen.value = false
    await Promise.all([loadMembers(), getCourse(courseId.value).then(response => { course.value = response.data })])
    proxy?.$modal.msgSuccess('课程负责人转移成功')
  } finally {
    transferringOwner.value = false
  }
}

function openCourseEditDialog() {
  if (!course.value) return
  Object.assign(courseEditForm, course.value)
  courseEditOpen.value = true
  nextTick(() => courseEditFormRef.value?.clearValidate())
}

async function submitCourseEdit() {
  const valid = await courseEditFormRef.value?.validate().catch(() => false)
  if (!valid) return
  savingCourseEdit.value = true
  try {
    await updateCourse({
      ...courseEditForm,
      courseCode: courseEditForm.courseCode?.trim(),
      courseName: courseEditForm.courseName?.trim(),
      courseCategory: courseEditForm.courseCategory?.trim(),
      description: courseEditForm.description?.trim(),
      remark: courseEditForm.remark?.trim()
    })
    const response = await getCourse(courseId.value)
    course.value = response.data
    courseEditOpen.value = false
    proxy?.$modal.msgSuccess('课程修改成功')
  } finally {
    savingCourseEdit.value = false
  }
}

function handleMockAction(name: string) {
  console.info(`${name}：下一步接入具体操作`)
}

function goBack() {
  router.push('/course')
}

loadDetail()

onBeforeUnmount(() => {
  parsePollTimers.forEach(timer => clearTimeout(timer))
  parsePollTimers.clear()
  buildPollTimers.forEach(timer => clearTimeout(timer))
  buildPollTimers.clear()
})
</script>

<style scoped lang="scss">
.course-detail {
  .detail-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e6eb;
  }

  .breadcrumb-line {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #909399;
    font-size: 13px;
  }

  h2 {
    margin: 8px 0;
    color: #1f2d3d;
    font-size: 22px;
    font-weight: 600;
  }

  .header-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    color: #606266;
    font-size: 13px;
  }

  .header-actions {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }

  .course-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 14px;
    }
  }

  .basic-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 14px;
  }

  .info-panel,
  .metric-panel,
  .knowledge-shell {
    border: 1px solid #e5e6eb;
    border-radius: 6px;
    background: #fff;
  }

  .info-panel {
    padding: 14px;
  }

  .panel-title {
    margin-bottom: 12px;
    color: #1f2d3d;
    font-size: 15px;
    font-weight: 600;
  }

  .metric-panel {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0;
    overflow: hidden;
  }

  .metric-item {
    min-height: 96px;
    padding: 18px;
    border-right: 1px solid #ebeef5;
    border-bottom: 1px solid #ebeef5;
  }

  .metric-item span {
    display: block;
    margin-bottom: 10px;
    color: #606266;
    font-size: 13px;
  }

  .metric-item strong {
    color: #1f2d3d;
    font-size: 26px;
  }

  .tab-toolbar {
    display: flex;
    gap: 8px;
    margin-bottom: 10px;
  }

  .tab-toolbar.compact {
    margin-top: -2px;
  }

  .document-layout {
    display: grid;
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 14px;
  }

  .module-tree {
    border: 1px solid #e5e6eb;
    border-radius: 6px;
    background: #fff;
    overflow: hidden;
  }

  .tree-title {
    padding: 12px 14px;
    border-bottom: 1px solid #ebeef5;
    color: #1f2d3d;
    font-weight: 600;
  }

  .module-tree :deep(.el-menu) {
    border-right: 0;
  }

  .module-tree :deep(.el-menu-item) {
    height: 42px;
    line-height: 42px;
  }

  .document-main {
    min-width: 0;
  }

  .document-search {
    margin-bottom: 6px;
  }

  .document-title {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .knowledge-shell {
    padding: 14px;
  }

  .knowledge-status {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) 160px 160px auto;
    gap: 12px;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;
  }

  .knowledge-status strong {
    display: block;
    margin-top: 4px;
    color: #1f2d3d;
  }

  .muted {
    color: #909399;
    font-size: 12px;
  }

  .download-hint {
    margin-left: 10px;
    color: #909399;
    font-size: 12px;
  }
}

@media (max-width: 1100px) {
  .course-detail {
    .basic-grid,
    .document-layout,
    .knowledge-status {
      grid-template-columns: 1fr;
    }

    .detail-header {
      flex-direction: column;
    }

    .header-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
}
</style>
