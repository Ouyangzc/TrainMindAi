# 学员端 MVP 实施计划

## 1. 文档目的

本文档将《学员端 MVP 详细设计方案》转换为可按顺序执行、验证和交付的工程任务，覆盖 PostgreSQL、Java 业务后端、FastAPI AI 服务、Vue 学员端、安全测试和联调验收。

实施遵循“小步闭环”原则：每一阶段完成后都必须具备可独立验证的业务结果，再进入下一阶段。

## 2. 实施基线

### 2.1 已确认范围

```text
course                    = 学员课程
course_module             = 课程目录模块
当前 published KB 快照    = 学员可见资料与 AI 检索范围
course_user               = 学员课程授权
```

学员端采用：

- “我的课程”作为入口。
- B 风格课程空间作为整体框架。
- C 风格 AI 学习助教作为默认页面。
- A 风格资料库作为课程内独立页面。

### 2.2 本计划采用的默认值

| 待确认项 | MVP 默认值 |
|---|---|
| 学习进度 | 不展示具有完成/考核含义的进度 |
| 学习记录 | 只记录最近访问和 AI 会话 |
| 手动完成 | 暂不实现 |
| AI 范围 | 只允许当前课程问答 |
| 无资料依据 | 拒答，不静默使用模型通用知识 |
| 登录后首页 | 先进入“我的课程” |
| 在线预览 | 第一阶段支持 PDF；其他格式先展示元数据 |
| PDF 定位 | 支持引用页码定位；精确段落高亮非 MVP 必须项 |
| 下载 | 由课程级开关控制，默认关闭 |
| 历史引用 | 保留引用元数据；无历史版本访问权限时提示已更新 |
| 终端 | 桌面端优先，完成基础响应式适配 |

### 2.3 明确不做

- 不新建另一套课程、章节和资料模型。
- 不实现培训班、考试、证书和掌握度。
- 不根据资料自动生成课程目录。
- 不读取管理端最新版本作为学员内容。
- 不允许跨课程检索。
- 不把“打开资料”自动认定为完成学习。

## 3. 当前工程基础

### 3.1 可直接复用

后端当前已有：

- `CourseAccessService`：课程级有效授权校验。
- `CourseUserMapper.selectEffectiveAccess`：已包含状态和授权时间校验。
- `PublishedCourseDocumentController`：已发布资料的初始只读入口。
- `IKnowledgeBaseService.selectPublishedDocuments`：当前发布快照资料查询能力。
- 课程、模块、资料、资料版本、知识库版本和课程成员管理闭环。
- 知识库草稿、构建、发布与回滚能力。

前端当前已有：

- Vue 3、Element Plus、RuoYi 动态路由和登录态。
- 管理端课程 API 与类型定义。
- 已通过静态原型确认的组合式学员端方向。

### 3.2 必须补齐

- 按当前用户查询“我的课程”。
- 学员专用 DTO 和接口，不复用管理端返回对象。
- 按发布快照组装模块目录。
- 资料详情、PDF 预览和下载权限策略。
- 课程内 AI 会话、问答及结构化引用。
- 学员端路由、布局和页面。
- 最近访问记录。
- 多课程、跨租户、过期授权及版本一致性测试。

## 4. 总体实施顺序

```text
T0 基线确认
-> T1 学员授权与我的课程
-> T2 发布快照目录与资料库
-> T3 PDF 预览与受控下载
-> T4 AI 会话与引用
-> T5 学员端组合页面
-> T6 最近访问
-> T7 联调、安全与验收
```

依赖关系：

- T1 是所有学员接口的权限基础。
- T2 是课程目录、资料库和 AI 引用的数据基础。
- T3 可与 T4 后半段并行，但引用跳转验收依赖 T3。
- T5 可先基于接口契约和 Mock 开发，真实联调依赖 T1 至 T4。
- T6 不阻塞核心问答闭环，可在 T5 后补齐。

## 5. T0：实施基线确认

### 5.1 目标

冻结 MVP 接口语义和现有数据库状态，避免实现过程中重复建模。

### 5.2 任务

#### T0-01：核对迁移状态

检查表及关键字段：

- `course`
- `course_module`
- `course_document`
- `course_document_version`
- `course_user`
- `knowledge_base`
- `knowledge_base_version`
- `knowledge_base_version_document`
- AI 侧 Chunk、问答与检索日志表

验证至少有一套测试数据：

```text
2 个学员
3 门课程
每门课程至少 2 个模块
至少 1 门有 published 版本
至少 1 门没有 published 版本
至少 1 条已过期授权
```

#### T0-02：确定学生接口命名空间

统一采用：

```text
/student/courses/**
```

不继续扩展 `/course/{courseId}/published-documents` 作为完整学员端接口。原接口可在迁移期保留，但内部应复用同一查询服务。

#### T0-03：冻结访问结果枚举

建议 Java 枚举或常量：

```text
available
content_preparing
not_started
expired
course_disabled
access_disabled
```

前端只根据枚举决定展示，不解析后端提示文案判断状态。

### 5.3 验收

- 数据表与现有迁移一致，无重复课程模型。
- 学员接口命名空间、状态枚举和错误码完成评审。
- 测试数据覆盖可用、无发布版和过期授权。

## 6. T1：学员授权与“我的课程”

### 6.1 目标

学员只能看到并进入自己有权访问的课程，支持一名学员拥有多门课程。

### 6.2 后端任务

#### T1-01：新增学员课程查询 DTO

建议新增：

```text
trainmind-system/.../domain/vo/student/StudentCourseVO.java
trainmind-system/.../domain/vo/student/StudentCourseDetailVO.java
```

最低字段：

- `courseId`
- `courseCode`
- `courseName`
- `courseCategory`
- `description`
- `ownerName`
- `availability`
- `accessStartAt`
- `accessEndAt`
- `publishedVersionId`
- `publishedVersionNo`
- `lastVisitedAt`（T6 前可为空）

不得向学员返回管理端专用字段、解析错误、对象存储路径和删除标志。

#### T1-02：新增按用户查询有效课程 SQL

扩展 `CourseUserMapper` 或新增学生查询 Mapper：

- 必须按 `tenant_id + user_id` 查询。
- 联表 `course`、`knowledge_base` 和当前 `knowledge_base_version`。
- 分别计算授权状态和内容状态。
- 课程列表排序：最近访问、课程排序、课程 ID。

不能调用管理端 `/course/list` 后在前端过滤。

#### T1-03：强化 CourseAccessService

在现有 `requireAccess(courseId, userId)` 基础上增加：

```text
requireStudentAccess(courseId, userId)
resolveStudentCourseContext(courseId, userId)
```

上下文至少返回：

- `tenantId`
- `courseId`
- `userId`
- 有效 `course_user`
- 当前 `knowledgeBaseId`
- 当前 `publishedVersionId`
- 课程可用状态

注意：当前有效授权 SQL 已判断 `start_at` 和 `end_at`，仍需同时校验 `course.status = active`。管理员绕过课程授权的逻辑不得自动套用到学生接口。

#### T1-04：新增学生课程 Controller 与 Service

建议新增：

```text
trainmind-admin/.../controller/student/StudentCourseController.java
trainmind-system/.../service/IStudentCourseService.java
trainmind-system/.../service/impl/StudentCourseServiceImpl.java
```

接口：

```http
GET /student/courses
GET /student/courses/{courseId}
```

认证采用当前登录用户，不接受请求参数指定 `userId`。

### 6.3 测试任务

- 用户 A 可见课程 1、2，不可见课程 3。
- 用户 B 只可见课程 3。
- 直接访问未授权 `courseId` 返回 403 语义错误。
- 授权未开始、已过期、停用分别返回明确状态。
- 课程停用后不能通过旧链接进入。
- 管理员身份调用学生接口时不应自动获得全部学生课程。
- 租户 A 用户不能访问租户 B 课程。

### 6.4 验收

- 多课程列表正确。
- 所有课程详情请求进行服务端授权。
- 无发布版课程显示 `content_preparing`，不返回资料。

## 7. T2：课程目录与资料库

### 7.1 目标

从当前发布知识库快照生成学员目录和资料库，确保二者与 AI 检索使用相同版本。

### 7.2 后端任务

#### T2-01：定义发布内容只读查询服务

建议新增或从 `IKnowledgeBaseService.selectPublishedDocuments` 抽取：

```text
IStudentPublishedContentService
```

职责：

1. 调用 `CourseAccessService` 获得学生课程上下文。
2. 固定当前 `publishedVersionId`。
3. 查询 `knowledge_base_version_document`。
4. 联表资料、资料版本和模块。
5. 输出学员 DTO。

所有学生内容接口必须复用该服务，避免目录、资料和引用分别写不同 SQL。

#### T2-02：课程目录接口

```http
GET /student/courses/{courseId}/outline
```

返回：

- `knowledgeBaseVersionId`
- `versionNo`
- 按排序输出的模块。
- 模块下发布资料。
- 无模块资料组成“通用资料”分组。

规则：

- 只展示未删除且启用的模块。
- 只展示当前发布快照包含的资料版本。
- 空模块默认不展示。
- 不能从 `latest_version_id` 取学员版本。

#### T2-03：资料列表接口

```http
GET /student/courses/{courseId}/documents?moduleId=&keyword=&fileExt=&pageNum=&pageSize=
```

筛选必须作用于发布快照，支持：

- 标题和原文件名关键词。
- 模块。
- 文件类型。
- 分页。

返回资料版本必须明确包含 `documentVersionId` 和 `versionNo`。

#### T2-04：资料详情接口

```http
GET /student/courses/{courseId}/documents/{documentId}
```

必须验证 `documentId` 存在于当前发布快照，不能只验证资料属于该课程。

### 7.3 数据库任务

优先复用现有索引。执行 `EXPLAIN ANALYZE` 检查学生资料查询；只有出现明确扫描问题时再新增复合索引，候选：

```text
knowledge_base_version_document(knowledge_base_version_id, module_id, document_id)
course_module(tenant_id, course_id, status, del_flag, sort_order)
```

不要在未测量前增加重复索引。

### 7.4 测试任务

- 管理端最新版本为 V4、发布快照为 V3 时，学员只拿到 V3。
- 管理端新增未发布资料后，学员目录与资料库不变化。
- 空模块不展示。
- 无模块资料进入“通用资料”。
- 停用模块在新发布版本下不展示。
- 搜索不会命中未发布资料。
- 越权 `documentId` 被拒绝。

### 7.5 验收

- 课程目录、资料库和发布快照逐条一致。
- 返回结果无解析状态和对象存储内部字段。
- 发布新版本后，新请求完整切换，不出现版本混读。

## 8. T3：PDF 在线预览与受控下载

### 8.1 目标

学员可以在线查看当前发布的 PDF，并从 AI 引用定位页码；下载默认关闭，可由课程配置开启。

### 8.2 数据库任务

为 `course` 增加：

```sql
allow_download boolean not null default false
```

要求：

- 迁移脚本可重复执行。
- Java Domain、Mapper、管理端表单和学生 DTO 同步。
- 管理端文案为“允许学员下载已发布资料”。
- 关闭仅影响学员下载，不影响管理员下载。

若产品希望避免当前阶段改表，可先用系统配置统一关闭下载，但正式课程级策略仍需后续补齐。推荐直接落课程字段。

### 8.3 后端任务

#### T3-01：预览接口

```http
GET /student/courses/{courseId}/documents/{documentId}/preview
```

处理：

1. 校验学生课程权限。
2. 从当前发布快照解析具体 `documentVersionId`。
3. 仅允许 PDF。
4. 返回短期签名 URL 或由后端流式输出。
5. 设置正确的 `Content-Type` 和内容安全头。

不得接受前端指定任意 `versionId` 后直接生成地址。

#### T3-02：下载接口

```http
GET /student/courses/{courseId}/documents/{documentId}/download
```

在预览权限之外额外校验 `course.allow_download = true`。下载的仍是当前发布快照版本，不是最新版本。

#### T3-03：页码定位

引用元数据中的 `pageStart` 映射为 PDF 查看器初始页。MVP 验收到页级定位即可，文本坐标高亮后续实现。

### 8.4 前端任务

- 优先使用项目可兼容的 PDF 查看组件或浏览器内嵌 PDF。
- 预览路由接收 `courseId + documentId + page`。
- 页面加载时再次从后端获取受控预览地址。
- 非 PDF 显示文件信息；仅在允许下载时展示下载按钮。
- 签名过期后允许重新申请，不把签名 URL持久化。

### 8.5 测试与验收

- PDF 可在线打开并定位指定页。
- 未发布版本无法预览。
- 课程关闭下载时下载接口拒绝。
- 课程允许下载时只能下载发布快照版本。
- 签名 URL 过期且不可跨资料复用。
- DOCX、PPTX、XLSX 不被错误当作 PDF 预览。

## 9. T4：AI 会话、问答与引用

### 9.1 目标

完成“当前课程提问 -> 基于发布版回答 -> 查看引用原文”的核心闭环。

### 9.2 数据库任务

先核对《AI 服务表结构设计（ai-schema）》中的会话、消息、检索日志和模型调用日志。如果缺少课程会话持久化，新增或补齐：

```text
chat_session
- tenant_id
- user_id
- course_id
- title
- status
- create_time / update_time

chat_message
- session_id
- role
- content
- knowledge_base_version_id
- status
- create_time

chat_message_citation
- message_id
- document_id
- document_version_id
- chunk_id
- page_start / page_end
- section_title
- quote
- rank / score
```

最终表名服从现有 AI Schema，不重复创建同义表。

### 9.3 Java 后端任务

#### T4-01：会话接口

```http
GET    /student/courses/{courseId}/chat/sessions
POST   /student/courses/{courseId}/chat/sessions
GET    /student/courses/{courseId}/chat/sessions/{sessionId}
POST   /student/courses/{courseId}/chat/sessions/{sessionId}/messages
```

每次请求校验：

- 会话属于当前登录用户。
- 会话属于路径中的课程。
- 当前用户仍有课程访问权限。

#### T4-02：AI 内部调用

Java 后端完成权限校验并解析 `knowledgeBaseVersionId` 后调用 FastAPI。前端不能直接调用 AI 内部接口。

请求至少包含：

```json
{
  "tenant_id": 1,
  "user_id": 10,
  "course_id": 100,
  "knowledge_base_version_id": 3,
  "session_id": 500,
  "message_id": 900,
  "question": "液压系统异常时如何处理？"
}
```

Java 记录最终使用的版本，不能信任前端传入版本。

#### T4-03：引用访问

```http
GET /student/courses/{courseId}/citations/{citationId}
```

返回引用保存时的资料版本、页码、章节和短片段。引用跳转前再次检查当前课程权限。

### 9.4 FastAPI 任务

- 检索强制过滤 `tenant_id + course_id + knowledge_base_version_id`。
- 不在没有检索证据时生成确定性课程答案。
- 返回结构化引用，而不是只在文本中拼文件名。
- 引用至少包含文档版本、Chunk、页码和章节。
- 写入检索日志、模型调用日志和错误原因。
- 保证回答引用只来自本次固定版本。
- 增加课程串库自动化测试。

推荐响应：

```json
{
  "answer": "……",
  "answerStatus": "grounded",
  "knowledgeBaseVersionId": 3,
  "citations": [],
  "requestId": "qa_xxx"
}
```

`answerStatus` 至少区分：

```text
grounded
insufficient_evidence
service_unavailable
```

### 9.5 测试与验收

- 同一问题在课程 A 中不能引用课程 B 的资料。
- 发布切换期间，单次请求的检索和引用版本一致。
- 无匹配 Chunk 时返回 `insufficient_evidence`。
- 引用可跳转到对应 PDF 页码。
- 伪造其他用户的 `sessionId` 被拒绝。
- AI 服务故障不影响资料库接口。

## 10. T5：学员端组合页面

### 10.1 目标

将已确认原型转化为正式 Vue 页面，并接入真实学生接口。

### 10.2 前端目录建议

```text
TrainMindFront/src/
├── api/student.ts
├── types/api/student.ts
├── views/student/
│   ├── courses/index.vue
│   ├── course-space/index.vue
│   ├── course-space/components/CourseSwitcher.vue
│   ├── course-space/assistant.vue
│   ├── course-space/outline.vue
│   ├── course-space/library.vue
│   ├── course-space/activities.vue
│   └── document-preview.vue
└── stores 或 composables/
    └── useStudentCourseContext.ts
```

遵循仓库实际状态管理约定，若无需全局 Store，优先使用课程空间父组件与 composable，避免过度引入状态。

### 10.3 页面任务

#### T5-01：我的课程

- 课程列表和状态分组。
- 最近访问优先。
- 内容准备中、尚未开始和已到期状态。
- 进入或继续课程。
- 无课程授权空状态。

#### T5-02：课程空间框架

- 当前课程切换器。
- AI 助教、课程目录、资料库和学习记录导航。
- 切换课程时清理旧课程的请求、会话和筛选状态。
- 路由中的 `courseId` 是当前上下文唯一来源。

#### T5-03：AI 学习助教

- 推荐问题和对话列表。
- 输入、发送、加载、失败重试。
- `grounded` 回答的引用卡片。
- `insufficient_evidence` 的拒答状态。
- 引用跳转资料预览。

#### T5-04：课程目录

- 展示模块说明、排序和模块资料。
- 不显示虚假进度。
- 点击资料进入预览或资料详情。

#### T5-05：资料库

- 关键词、模块和文件类型筛选。
- 显示当前发布版资料信息。
- 支持 AI 引用跳入后的高亮和页码定位。
- 根据 `allowDownload` 决定下载按钮。

### 10.4 路由和菜单

建议学生入口：

```text
/student/courses
/student/courses/:courseId/assistant
/student/courses/:courseId/outline
/student/courses/:courseId/library
/student/courses/:courseId/activities
/student/courses/:courseId/documents/:documentId/preview
```

具体菜单由 RuoYi 动态路由或固定学生路由承载，但必须：

- 学员角色只进入学员端菜单。
- 管理端课程权限不能代替学生课程数据权限。
- 页面刷新后能恢复当前课程和子页面。

### 10.5 前端验收

- 一名学员可在课程之间切换且数据不串。
- 直接刷新课程子页面可以恢复上下文。
- 快速切换课程时旧请求结果不会覆盖新课程。
- 所有加载、空、失败和权限失效状态有明确反馈。
- 窄屏下可以完成课程切换、提问和资料查阅。

## 11. T6：最近访问记录

### 11.1 目标

为“继续学习”和最近活动提供事实数据，不引入完成度语义。

### 11.2 数据库建议

新增轻量活动表：

```text
student_learning_activity
- id
- tenant_id
- user_id
- course_id
- activity_type      course_view / module_view / document_view / chat
- target_id
- occurred_at
- metadata_json
- 统一审计字段
```

如果现有审计或行为表可以满足按用户和课程查询，可复用，不重复建表。

### 11.3 接口

```http
GET  /student/courses/{courseId}/activities
POST /student/courses/{courseId}/activities
```

服务端从登录态确定用户。写活动前校验课程访问权限，对高频浏览事件做去重或节流。

### 11.4 验收

- 我的课程可按最近访问排序。
- 课程活动展示访问资料和 AI 会话。
- 不展示“已完成 68%”等无可靠依据的数据。
- 用户只能查看自己的活动。

## 12. T7：联调、安全与验收

### 12.1 联调数据矩阵

至少准备：

| 数据 | 用途 |
|---|---|
| 学员 A + 课程 1、2 | 多课程切换 |
| 学员 B + 课程 2 | 同课程不同用户 |
| 未授权课程 3 | 越权验证 |
| 无发布版课程 | 内容准备中 |
| V3 已发布、V4 已解析 | 快照一致性 |
| 已过期授权 | 有效期验证 |
| 另一租户课程 | 租户隔离 |
| PDF 含确定页码答案 | 引用定位 |
| 无相关内容问题 | AI 拒答 |

### 12.2 自动化测试层次

#### Java 单元与集成测试

- 授权状态计算。
- 当前发布版解析。
- 目录组装。
- 发布资料筛选。
- 预览和下载权限。
- 会话归属校验。

#### Mapper 测试

- 多租户条件。
- 授权起止时间边界。
- 发布快照版本选择。
- 关键词和模块筛选。

#### FastAPI 测试

- 版本过滤。
- 跨课程隔离。
- 无依据拒答。
- 引用结构完整性。

#### 前端测试

- 课程上下文切换。
- 路由恢复。
- 旧请求竞争处理。
- API 错误和空状态。

#### 端到端测试

```text
登录
-> 我的课程
-> 进入课程
-> AI 提问
-> 查看引用
-> 定位 PDF 页码
-> 返回资料库搜索
-> 切换另一课程
-> 验证上下文已切换
```

### 12.3 安全测试

- 枚举 `courseId`、`documentId`、`sessionId`、`citationId`。
- 已获取预览 URL 在签名过期后失效。
- 下载开关关闭时接口不可绕过。
- 授权到期后已打开页面的新请求立即失败。
- 用户无法通过篡改版本 ID 访问草稿或历史文件。
- AI 内部接口不直接暴露给浏览器。
- 日志不记录文件凭据、Token 或完整敏感问答正文（按审计策略脱敏）。

### 12.4 性能基线

MVP 建议目标，不作为未经压测的保证：

- 我的课程 P95 小于 500ms。
- 目录与资料列表 P95 小于 800ms。
- PDF 预览首字节 P95 小于 2s（不含大文件完整加载）。
- AI 首次响应状态在 3s 内可见，完整回答按模型能力单独记录。
- 至少完成 20 个并发学员的基础压测。

## 13. 任务清单与完成定义

| 编号 | 任务 | 依赖 | 完成定义 |
|---|---|---|---|
| T0-01 | 核对表结构与测试数据 | 无 | 数据矩阵可重复初始化 |
| T0-02 | 冻结学生接口命名 | 无 | 接口评审通过 |
| T1-01 | 学员课程 DTO | T0 | 字段无管理端泄漏 |
| T1-02 | 我的课程查询 | T1-01 | 多课程和有效期测试通过 |
| T1-03 | 学生访问上下文 | T1-02 | 所有学生接口可复用 |
| T1-04 | 学生课程接口 | T1-03 | 列表和详情联调通过 |
| T2-01 | 发布内容只读服务 | T1-03 | 固定发布版查询通过 |
| T2-02 | 课程目录接口 | T2-01 | 模块和快照一致 |
| T2-03 | 资料列表接口 | T2-01 | 搜索筛选分页通过 |
| T2-04 | 资料详情接口 | T2-01 | 越权测试通过 |
| T3-01 | 下载策略字段 | T0 | 迁移与管理端配置通过 |
| T3-02 | PDF 预览接口 | T2-04 | 发布版 PDF 可预览 |
| T3-03 | 下载接口 | T3-01,T2-04 | 开关与版本测试通过 |
| T4-01 | 会话模型与接口 | T1-03 | 会话归属测试通过 |
| T4-02 | AI 版本化问答 | T2-01,T4-01 | 单课程检索通过 |
| T4-03 | 结构化引用 | T3-02,T4-02 | 引用页码跳转通过 |
| T5-01 | 我的课程页面 | T1-04 | 多状态展示通过 |
| T5-02 | 课程空间框架 | T5-01 | 切换与刷新通过 |
| T5-03 | AI 助教页面 | T4 | 问答闭环通过 |
| T5-04 | 目录与资料库页面 | T2,T3 | 查阅闭环通过 |
| T6-01 | 最近访问记录 | T1 | 最近活动联调通过 |
| T7-01 | 全链路与安全验收 | 全部 | 验收用例全部通过 |

单项任务只有在以下条件全部满足时才算完成：

1. 实现代码完成。
2. 正常和异常测试通过。
3. 接口文档或类型定义同步。
4. 不引入未授权的数据访问路径。
5. 相关设计或实施文档状态已更新。

## 14. 推荐的首个实施批次

第一批不要立即做 AI 页面，先完成可验证的数据与权限闭环：

```text
T0-01 测试数据与表结构确认
-> T1-01 学员课程 DTO
-> T1-02 我的课程查询
-> T1-03 学生访问上下文
-> T1-04 我的课程接口
-> 后端权限冒烟测试
```

第一批验收结果应是：

> 使用不同学员账号调用 `/student/courses`，能够得到各自正确的多课程列表；访问未授权、未开始、过期和停用课程时得到明确且不可绕过的结果。

完成该批次后，再实施课程目录与资料库。这样可以避免先做页面，最后才发现学员权限和发布快照数据源不可靠。

## 15. 风险与控制措施

| 风险 | 影响 | 控制措施 |
|---|---|---|
| 复用管理端列表接口 | 未发布内容泄漏 | 建立独立学生查询服务和 DTO |
| 使用 `latest_version_id` | 学员看到未发布版本 | 所有学生内容固定发布快照 |
| 只在前端校验授权 | ID 枚举越权 | 每个后端入口重新校验 |
| 课程切换请求竞争 | 页面串课 | 取消旧请求并校验响应 courseId |
| AI 使用错误版本 | 答案引用不一致 | Java 固定版本，AI 强过滤并回传版本 |
| 签名 URL 长期有效 | 文件泄漏 | 短期签名、禁止持久化 |
| 打开资料即算完成 | 学习数据失真 | MVP 仅记录访问事实 |
| 过早引入 LMS 模型 | 范围和维护成本膨胀 | 考试、班级和掌握度后置 |

## 16. 交付物

MVP 完成时应交付：

- 数据库迁移及回滚说明。
- 学员端 Java API、Service、Mapper 和 DTO。
- FastAPI 课程问答与结构化引用能力。
- Vue 学员端正式页面。
- PDF 预览和课程级下载控制。
- 单元、集成及端到端测试。
- 接口文档和错误码说明。
- 测试数据初始化说明。
- 安全验证记录。
- 更新后的实施进度与遗留问题清单。

本文档未授权自动开始业务代码修改。实际实施按任务编号逐项进行，每个批次完成后验收再继续。

## 17. 当前实施进度

更新时间：2026-07-22。

| 任务 | 状态 | 结果 |
|---|---|---|
| T0-01 表结构与测试数据核对 | 部分完成 | 真实库现有 1 门已发布课程、1 个有效学员授权；多课程、未发布和过期授权测试数据仍缺 |
| T0-02 学生接口命名空间 | 已完成 | 采用 `/student/courses/**` |
| T0-03 访问状态枚举 | 已完成 | 查询输出六种稳定状态值 |
| T1-01 学员课程 DTO | 已完成 | 新增只读课程 VO 和可信课程上下文 |
| T1-02 我的课程查询 | 已完成 | 按租户、登录用户和 `student` 授权查询，区分课程及发布状态 |
| T1-03 学生访问上下文 | 已完成 | 管理员不在学生接口中自动绕过课程授权 |
| T1-04 学生课程接口 | 已完成 | 新增列表与详情接口 |
| 首批验证 | 已完成 | Maven 编译、Spring 启动、MyBatis 加载和真实库正常路径只读查询通过；完整状态矩阵测试数据仍待补齐 |
| T2-01 发布内容只读服务 | 已完成 | 所有学生内容先校验学员授权并固定当前发布版本 |
| T2-02 课程目录接口 | 已完成 | 按启用模块分组发布快照资料，无模块资料归入通用资料 |
| T2-03 资料列表接口 | 已完成 | 支持模块、关键词、文件类型和分页，分页在授权校验后启动 |
| T2-04 资料详情接口 | 已完成 | 资料必须存在于当前课程的当前发布快照 |
| T2 验证 | 已完成 | 编译、打包、Spring/MyBatis 运行时启动、未认证拦截和真实发布快照 SQL 通过 |
| T3-01 课程下载策略 | 已完成 | 新增 `course.allow_download`，默认关闭；管理端新增与编辑表单可配置 |
| T3-02 PDF 在线预览 | 已完成 | 只允许预览当前发布快照中的 PDF，响应使用 inline 和 no-store |
| T3-03 受控下载 | 已完成 | 课程开关开启后才能下载当前发布快照版本 |
| T3 验证 | 部分完成 | 数据库迁移、前后端构建、Spring 启动和 OpenAPI 路由注册通过；当前真实发布快照只有 PPTX，PDF 文件流仍待样本验证 |
| T4-01 会话模型与接口 | 已完成 | 新增课程内会话、用户消息、助手消息及会话归属校验 |
| T4-02 AI 版本化问答 | 已完成 | Java 后端注入当前发布版本调用 FastAPI；空检索结果明确拒答，服务异常降级且消息可追溯 |
| T4-03 结构化引用 | 已完成 | 引用仅在文档及文档版本均属于当前发布快照时落库，并提供归属受控的引用详情接口 |
| T4 验证 | 部分完成 | 三张业务表迁移、AI 定向测试与 Ruff、Java 构建、Spring/MyBatis 启动及 OpenAPI 路由注册通过；真实模型回答、真实引用页码跳转仍待联合服务和 PDF 样本验证 |
| T5-01 我的课程页面 | 已完成 | 接入真实学员课程接口，按六种稳定状态分组展示，包含加载失败重试、无授权空状态和窄屏布局；进入课程联动依赖 T5-02 |
| T5-02 课程空间框架 | 已完成 | 接通课程入口和四类子路由，以路由 `courseId` 为唯一上下文；支持课程切换、刷新恢复、旧请求失效、越权及不可用课程拦截和窄屏导航 |
| T5-03 AI 学习助教 | 已完成 | 接入真实会话列表、历史消息、新对话和同步问答；展示依据不足与服务降级状态，支持失败重试、结构化引用卡片及携资料页码跳转资料库 |
| T5-03 验证 | 部分完成 | 前端生产构建、增量类型检查和前后端契约核对通过；真实模型回答和引用预览联动仍待 AI 服务及 T5-04 资料页面联合验证 |
| T5-04 课程目录与资料库 | 已完成 | 接入当前发布快照目录、资料搜索、模块与类型筛选及分页；支持 AI 引用资料高亮、PDF Blob 鉴权预览与页码定位，并按课程开关控制下载入口 |
| T5-04 验证 | 部分完成 | 前端生产构建、增量类型检查和接口契约检查通过；真实快照只有 PPTX，PDF 浏览器预览与引用页码仍待 PDF 样本验证 |
| T6-01 最近访问与学习记录 | 已完成 | 新增事实活动表及查询/上报接口，60 秒内同目标去重；课程列表按最近访问优先，记录课程进入、发布资料查阅和 AI 提问，不推导完成率或学习时长 |
| T6 验证 | 已完成 | 数据库迁移、前后端生产构建、增量类型检查、Spring/MyBatis 运行启动和 OpenAPI 路由注册通过 |
| T7-01 核心联调与安全验收 | 已完成 | 新增可重复验收夹具与冒烟脚本；真实登录验证系统学员角色、两门可用课程、准备中/过期状态、跨租户与未授权课程拒绝、活动归属、下载 403、AI 降级和跨用户会话拒绝 |
| T7-02 全量回归 | 已完成 | AI 服务 31 项测试通过、Ruff 通过、Java 构建通过、前端生产构建及增量类型检查通过 |
| T7-03 PDF/真实模型/性能 | 待完成 | 当前缺少已发布 PDF 样本和运行中的真实模型服务；20 并发及 P95 基线尚未执行，不作为当前版本已达成指标 |
