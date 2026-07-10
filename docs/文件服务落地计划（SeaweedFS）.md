# 文件服务落地计划（SeaweedFS）

## 目标

为 TrainMindAi 提供可商用化友好的文件服务底座，支撑用户上传课件资料、后端元数据管理、AI 服务下载解析、后续检索与问答引用。

本阶段选择 SeaweedFS 作为本地与私有化部署候选组件，通过 S3 兼容接口接入业务系统。业务代码只依赖标准对象存储能力，不绑定 SeaweedFS 或 MinIO 私有 API。

本计划只负责对象存储和资料文件服务，不负责知识库草稿、Chunk、索引、发布和回滚。知识库治理统一见《知识库治理设计方案》。

## 当前状态

- 已在本机以 SeaweedFS 4.38 `weed mini` 模式启动开发服务。
- 已安装并启用用户级 systemd 服务：`seaweedfs-trainmind.service`。
- 已开启当前用户 linger：`Linger=yes`。WSL 发行版启动后，用户级服务可自动拉起。
- S3 端点：`http://127.0.0.1:8333`
- Admin UI：`http://127.0.0.1:23646`
- 已完成 S3 Signature V4 冒烟：`PUT /trainmind-docs/codex-smoke.txt` 成功，随后 `GET` 返回原始内容。
- 未提交二进制和数据目录；`.tools/` 已由 `.gitignore` 忽略。

## 选型结论

- 默认本地开发与私有化部署使用 SeaweedFS。
- 接入层使用 S3 兼容协议，后续可替换为 SeaweedFS、MinIO、AWS S3、阿里云 OSS S3 兼容接口或其他对象存储。
- Java 后端服务命名为 `ObjectStorageService` / `S3ObjectStorageService`，不要命名为 `MinioService`。
- MVP 的 AI 服务固定使用自身配置的 Bucket，只接收 `object_name`、`checksum_md5` 等存储中立字段，不允许请求指定任意 Bucket，也不直接感知具体对象存储实现。
- AI 服务配置统一使用 `object_storage_*`，客户端和下载方法使用 `S3ObjectStorageClient`、`download_from_object_storage` 等存储中立名称，不使用 `minio_*` 业务命名。
- 状态展示和筛选统一接入 RuoYi 字典，后端业务流转保留常量校验，避免在页面和业务代码里散落中文标签或魔法字符串。

## 本地部署

已提供本地脚本：

```bash
./scripts/seaweedfs-start.sh
./scripts/seaweedfs-stop.sh
```

也已提供用户级 systemd 服务模板：

```bash
deploy/systemd/seaweedfs-trainmind.service
```

当前服务以用户级 systemd 运行，避免写入系统目录。WSL 启动且当前用户的 systemd user manager 运行后，服务会随 `default.target` 自动启动。

安装后的常用命令：

```bash
systemctl --user status seaweedfs-trainmind.service
systemctl --user restart seaweedfs-trainmind.service
systemctl --user stop seaweedfs-trainmind.service
journalctl --user -u seaweedfs-trainmind.service -f
```

开机自启说明：

- 在 WSL 内，`systemd` 已启用，`seaweedfs-trainmind.service` 已 `enable --now`。
- 当前用户已执行 `loginctl enable-linger oyang`，状态为 `Linger=yes`。
- WSL 不是传统物理机服务模型；Windows 开机后，如果 WSL 发行版本身没有被启动，Linux 内的 systemd 服务也不会运行。需要 Windows 开机即启动 WSL 时，可额外配置 Windows 任务计划程序执行 `wsl -d <发行版名称> --user oyang true`。

宿主机访问说明：

- SeaweedFS 绑定在 WSL 内 `127.0.0.1`，避免暴露到局域网。
- 在常规 WSL2 localhost 转发可用时，Windows 宿主机浏览器可以访问 `http://127.0.0.1:23646` 或 `http://localhost:23646`。
- 如果 Windows 宿主机无法访问，优先检查 WSL localhost 转发或改用 Windows 端口代理；不要直接改成 `0.0.0.0` 对外暴露，除非明确需要局域网访问并已配置鉴权、防火墙和反向代理。

默认端点：

| 服务 | 地址 | 用途 |
|---|---|---|
| S3 Endpoint | `http://localhost:8333` | 后端和 AI 服务对象读写 |
| Filer UI | `http://localhost:8888` | 本地文件浏览 |
| Master UI | `http://localhost:9333` | 集群和卷状态 |
| Admin UI | `http://localhost:23646` | 管理界面 |

默认配置：

| 配置项 | 默认值 |
|---|---|
| Bucket | `trainmind-docs` |
| Access Key | `trainmind` |
| Secret Key | `trainmind-secret` |
| 数据目录 | `.tools/seaweedfs-data` |
| 日志文件 | `.tools/logs/seaweedfs.log` |

可通过环境变量覆盖：

```bash
SEAWEEDFS_BUCKET=trainmind-docs \
SEAWEEDFS_ACCESS_KEY=trainmind \
SEAWEEDFS_SECRET_KEY=trainmind-secret \
SEAWEEDFS_ADMIN_PASSWORD=trainmind-admin \
./scripts/seaweedfs-start.sh
```

### 凭据管理

文档中的默认凭据只允许本地开发使用：

```text
Access Key: trainmind
Secret Key: trainmind-secret
Admin Password: trainmind-admin
```

测试和生产环境规则：

- S3 Access Key、Secret Key 和 Admin UI 密码必须通过环境变量、密钥文件或外部密钥管理服务注入。
- 不得将测试或生产密钥写入 Git、应用 YAML、镜像或 systemd 服务模板。
- 非开发环境检测到上述默认凭据时，服务必须拒绝启动。
- MVP 默认由 Java 后端和 AI 服务共用一套业务 S3 凭据，授予 `trainmind-docs` 所需的读取、写入和删除权限。
- Admin UI 使用独立管理员凭据，不与 Java 后端或 AI 服务共用。
- 后续需要最小权限隔离时，再将 AI 服务拆分为独立只读凭据。
- 密钥轮换时先部署新凭据并验证读写，再撤销旧凭据，避免中断上传和解析任务。

AI 服务配置命名：

```text
OBJECT_STORAGE_ENDPOINT
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
OBJECT_STORAGE_BUCKET
OBJECT_STORAGE_SECURE
```

AI 服务实施时优先使用 `boto3` 访问 SeaweedFS S3 API。业务配置、类名和方法名保持存储中立，不依赖 SeaweedFS 或 MinIO 私有 API。

## 业务链路

目标闭环：

```text
前端选择课程并上传文件
  -> Java 后端校验文件和权限
  -> Java 后端上传对象存储
  -> Java 后端写入文档和文档版本元数据
  -> 管理员或课程讲师手动触发解析
  -> Java 后端调用 AI 服务创建解析任务
  -> AI 服务从对象存储下载文件
  -> AI 服务解析文档并保存解析结果
  -> 前端展示任务状态和解析结果
```

后续的“选择已解析资料 -> 构建 Chunk 和索引 -> 人工发布”属于知识库治理边界，不进入文件服务事务。

## 数据模型建议

业务库建议至少包含以下表或等价字段。

### 文档表

`course_document`

| 字段 | 说明 |
|---|---|
| `id` | 文档 ID |
| `tenant_id` | 租户 ID，第一阶段默认 1 |
| `course_id` | 所属课程 |
| `module_id` | 所属模块，可为空，空表示课程公共资料 |
| `title` | 文档标题 |
| `status` | `active / archived`，删除不使用状态表达 |
| `latest_version_id` | 最新文档版本 |
| `del_flag` | 删除标志，`0` 存在，`2` 删除 |
| `create_by` | 创建人 |
| `create_time` | 创建时间 |
| `update_by` | 更新人 |
| `update_time` | 更新时间 |
| `remark` | 备注 |

归档表示资料退出当前默认维护列表，但仍保留历史记录和对象文件。删除统一走 `del_flag = '2'` 逻辑删除，不立即物理删除对象存储文件。

### 文档版本表

`course_document_version`

| 字段 | 说明 |
|---|---|
| `id` | 文档版本 ID |
| `tenant_id` | 租户 ID，第一阶段默认 1 |
| `document_id` | 文档 ID |
| `course_id` | 冗余课程 ID，便于查询 |
| `module_id` | 冗余模块 ID，便于查询 |
| `version_no` | 版本号 |
| `original_filename` | 原始文件名 |
| `file_ext` | 文件扩展名 |
| `content_type` | MIME 类型 |
| `file_size` | 文件大小 |
| `checksum_md5` | 文件 MD5 |
| `bucket` | 对象存储 bucket |
| `object_name` | 对象存储 key |
| `parse_task_id` | AI 解析任务 ID |
| `status` | `uploaded / parsing / parsed / failed / archived` |
| `parse_error_message` | 解析失败原因 |
| `del_flag` | 删除标志，`0` 存在，`2` 删除 |
| `create_by` | 上传人 |
| `create_time` | 上传时间 |
| `update_by` | 更新人 |
| `update_time` | 更新时间 |
| `remark` | 备注 |

文档版本由系统自动创建：首次上传创建 `v1`，上传新版本时自动取 `max(version_no) + 1`。用户不手工输入版本号。

### 字典配置

建议新增以下 RuoYi 字典类型，统一管理状态标签、筛选下拉和表格 Tag：

| 字典类型 | 字典名称 | 对应字段 |
|---|---|---|
| `trainmind_course_status` | 课程状态 | `course.status` |
| `trainmind_course_module_status` | 课程模块状态 | `course_module.status` |
| `trainmind_course_document_status` | 课程资料状态 | `course_document.status` |
| `trainmind_document_version_status` | 资料版本状态 | `course_document_version.status` |

核心字典值：

| 字典类型 | 标签 | 值 | 样式 |
|---|---|---|---|
| `trainmind_course_document_status` | 正常 | `active` | `success` |
| `trainmind_course_document_status` | 归档 | `archived` | `info` |
| `trainmind_document_version_status` | 待解析 | `uploaded` | `info` |
| `trainmind_document_version_status` | 解析中 | `parsing` | `warning` |
| `trainmind_document_version_status` | 已解析 | `parsed` | `success` |
| `trainmind_document_version_status` | 失败 | `failed` | `danger` |
| `trainmind_document_version_status` | 已归档 | `archived` | `info` |

字典只负责展示和可配置筛选。后端仍需要定义状态常量，用于权限判断、学员可见过滤、解析流转和数据一致性校验。

## Object Key 规范

建议使用稳定、可追踪、避免中文路径依赖的对象 key：

```text
tenants/{tenant_id}/courses/{course_id}/modules/{module_id}/documents/{document_id}/versions/{version_id}/{uuid}.{ext}
```

示例：

```text
tenants/1/courses/100/modules/10/documents/200/versions/300/018f6f2e-....pdf
```

课程公共资料使用：

```text
tenants/{tenant_id}/courses/{course_id}/modules/public/documents/{document_id}/versions/{version_id}/{uuid}.{ext}
```

文件名展示使用数据库里的 `original_filename`，不要依赖对象 key 还原。

## 后端接口计划

第一阶段实现最小闭环：

| 接口 | 方法 | 说明 |
|---|---|---|
| `/course/{courseId}/documents/upload` | `POST` | 上传文件并创建文档和 v1 版本 |
| `/course/{courseId}/documents/{documentId}/versions` | `POST` | 上传新版本，系统自动递增版本号 |
| `/course/{courseId}/documents` | `GET` | 查询资料列表 |
| `/course/{courseId}/documents/{documentId}` | `GET` | 查询文档详情 |
| `/course/{courseId}/documents/{documentId}/versions` | `GET` | 查询版本列表 |
| `/course/{courseId}/documents/{documentId}/versions/{versionId}/parse` | `POST` | 手动触发解析 |
| `/course/{courseId}/documents/{documentId}/versions/{versionId}/parse-task` | `GET` | 查询解析任务状态 |
| `/course/{courseId}/documents/{documentId}/versions/{versionId}/download` | `GET` | 下载原文件 |
| `/course/{courseId}/documents/{documentId}` | `DELETE` | 逻辑删除文档 |

上传接口处理顺序：

1. 校验登录、课程权限、文件类型、文件大小。
2. 计算 MD5。
3. 创建文档和文档版本记录，生成 `object_name`。
4. 上传对象存储。
5. 标记 `status = uploaded`，等待管理员或课程讲师手动解析。

上传成功后不自动解析。管理员或课程讲师/负责人点击“手动解析”后，业务后端再把版本状态更新为 `parsing` 并调用 AI 服务。

AI 服务解析接口：

```http
POST /internal/v1/documents/{document_version_id}/parse
```

请求字段：

```json
{
  "course_id": 100,
  "document_id": 200,
  "object_name": "tenants/1/courses/100/modules/10/documents/200/versions/300/file.pdf",
  "file_ext": "pdf",
  "checksum_md5": "..."
}
```

MVP 只使用 `trainmind-docs` 一个 Bucket：

- Java 数据库仍保存每个资料版本的 `bucket`。
- AI 服务通过环境配置固定 `trainmind-docs`，解析请求不传 `bucket`。
- Java 调用 AI 服务前校验资料版本记录的 Bucket 与允许配置一致。
- 后续确需多 Bucket 时，再扩展接口并增加 Bucket 允许列表。

## 兼容性要求

只依赖以下 S3 标准能力：

- `PutObject`
- `GetObject`
- `HeadObject`
- `DeleteObject`
- Bucket 初始化

暂不依赖：

- MinIO Admin API
- MinIO Console
- 对象锁定 Object Lock
- 复杂 Lifecycle
- 复杂 Bucket Policy
- 事件通知
- ETag 等同 MD5 的假设
- S3 Multipart Upload
- 断点续传

MVP 单文件最大 200MB，Java 后端通过一次 `PutObject` 写入 SeaweedFS。上传失败时本次请求整体失败，用户重新上传；允许 S3 SDK执行底层有限重试，但不实现业务层分片续传。

## 验收清单

- SeaweedFS 本地 S3 端点可启动。
- 后端可上传 PDF、DOCX、PPTX、XLSX。
- 数据库记录 `bucket`、`object_name`、`checksum_md5`。
- AI 服务可按 `object_name` 下载文件。
- 上传后不自动解析，手动解析后能生成 AI 解析任务。
- 管理端可查看上传状态和解析状态。
- 解析成功不会自动改变学员资料范围。
- 学员端只展示当前已发布知识库版本纳入的资料，不展示解析状态。
- 停止并重启 SeaweedFS 后，已上传文件仍可读取。
- 200MB 以内文件可通过单次 `PutObject` 上传。

## 风险和处理

| 风险 | 处理 |
|---|---|
| S3 兼容实现与 AWS/MinIO 存在细节差异 | 编写对象存储兼容测试，不绑定厂商私有能力 |
| 商用化许可证风险 | 默认选择 Apache-2.0 的 SeaweedFS，保留 S3 抽象 |
| 对象存储和数据库元数据不一致 | 上传失败回滚元数据；删除统一设置 `del_flag = '2'`，物理对象由后台清理 |
| 大文件上传中断 | MVP 整体失败后重新上传；后续阶段再支持 S3 Multipart Upload 和断点续传 |
| AI 解析失败 | 保留失败任务、错误原因和重试入口 |

## 对象清理策略

MVP 只执行数据库逻辑删除，不提供立即物理删除对象的按钮，也不自动清理 SeaweedFS 对象。

后续物理清理任务必须遵守：

- 被当前发布、历史归档或活动知识库版本引用的资料对象禁止清理。
- 未被任何知识库版本引用且已逻辑删除的对象才可进入待清理范围。
- 对象必须经过保留期后才能清理，具体天数在清理任务实施时确定。
- 实际删除对象前必须再次检查知识库版本引用，避免扫描后引用关系发生变化。
- 清理成功或失败都记录对象位置、资料版本、操作时间和结果，形成审计日志。
- 对象删除失败不删除数据库元数据，由后续任务重试。

## 实施步骤

1. 完成本地 SeaweedFS 启动脚本和开发配置。
2. 后端新增对象存储配置与 `ObjectStorageService`。
3. 新增课程、模块、资料和解析状态字典。
4. 后端新增文档和文档版本表。
5. 后端实现上传接口和解析任务触发。
6. AI 服务文件下载适配 S3 兼容配置。
7. 前端新增课程资料上传页面，并使用 RuoYi 字典渲染状态。
8. 增加兼容性测试和端到端冒烟。
