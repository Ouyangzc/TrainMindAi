# TrainMindAi ai-service 任务路线图设计

> 日期: 2026-06-22
> 状态: Phase 1 已实施，Phase 2 待开始
> 对应项目: `trainmind-ai-service` (FastAPI Python AI 服务)

---

## 1. 现状概述

当前项目状态（脚手架 + MVP 基础）：

| 模块 | 状态 |
|------|------|
| 核心基础设施 (config/db/redis/security/errors/logging) | ✅ 完成 |
| 数据库模型 + Alembic 迁移 (3 个版本, 16 张表) | ✅ 完成 |
| API stub 路由 | ✅ 完成；文档解析入队契约已补齐 |
| Gateway 客户端 (LLM / Embedding) | ✅ 完成 |
| 文档解析 (Markdown/PDF/PPTX/DOCX/XLSX) | ✅ Phase 1 完成 |
| Chunk 策略 (title / fixed_size) | ⚠️ MVP |
| 混合检索 (pgvector + PG FTS) | ⚠️ MVP |
| RAG 问答 (同步) | ⚠️ MVP |
| Worker 管道 (parse→chunk→keyword→embedding) | ⚠️ MVP；parse 已支持 MinIO + Markdown fallback |
| 关键词索引 (jieba + PG FTS tsvector) | ⚠️ MVP |
| SSE 流式问答 | ❌ 占位 |
| PDF/PPTX/DOCX/XLSX 解析 | ✅ Phase 1 完成 |
| AI 出题 | ❌ 占位 |
| 错题诊断 | ❌ 占位 |
| 简答评分 | ⚠️ 草稿实现 |
| RAG 离线评估 | ❌ 占位 |
| 健壮性 (重试/并发/降级/可观测) | ⚠️ Phase 1 已补解析超时/下载校验；并发/降级/指标仍待后续阶段 |
| 测试覆盖 | ⚠️ Phase 1 新增解析/API/Worker 测试；coverage 报告待安装 pytest-cov |

## 2. 总体架构

```
数据流方向 →
┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐
│Phase 1   │→ │Phase 2   │→ │Phase 3    │→ │Phase 4    │→ │Phase 5   │
│文档解析   │  │知识库构建 │  │检索 + RAG │  │出题/诊断  │  │RAG离线评估│
│管道      │  │管道健壮化 │  │增强       │  │评分       │  │          │
├──────────┤  ├──────────┤  ├───────────┤  ├───────────┤  ├──────────┤
│• PDF     │  │• Chunk   │  │• 流式SSE  │  │• AI出题   │  │• 评估    │
│• PPTX    │  │  策略增强│  │• 多轮对话 │  │• 错题诊断 │  │  runner  │
│• DOCX    │  │• Worker  │  │• 引用校验 │  │• 简答评分 │  │• 指标    │
│• XLSX    │  │  并发控制│  │• 降级策略 │  │• Schema   │  │  计算    │
│• MinIO   │  │• 增量更新│  │           │  │  校验     │  │• 报告    │
│• 超时重试 │  │• 指数退避│  │           │  │          │  │          │
└──────────┘  └──────────┘  └───────────┘  └───────────┘  └──────────┘
     ↑              ↑              ↑              ↑              ↑
  每段内嵌: 错误处理 + 单元测试 + 集成测试 + 边界测试
```

### 2.1 设计原则

- **增量交付**: 每阶段产出独立可验证
- **健壮性内建**: 错误处理/重试/降级与功能在同一阶段实现
- **配置优先**: 行为可配置 (chunk 策略/检索策略/prompt 模板)，不改代码
- **可观测**: 每步进度可查，指标可监控
- **向后兼容**: 不破坏现有 API 契约

### 2.2 依赖关系

```
Phase 1 → Phase 2 → Phase 3 ─→ Phase 5
                    └─→ Phase 4
```

- Phase 1-2 是前置依赖 (文档可解析 → 知识库可构建)
- Phase 3 依赖 Phase 2 (检索依赖索引就位)
- Phase 4 依赖 Phase 3 (出题依赖检索，问答依赖 RAG)
- Phase 5 依赖 Phase 2 + Phase 3 (评估依赖检索 + RAG)

---

## 3. 阶段 1: 文档解析管道

### 目标

将当前仅支持 Markdown 的解析器扩展为支持 PDF/PPTX/DOCX/XLSX，集成 MinIO 文件下载，具备超时和错误容错。

### Phase 1 前置契约

Phase 1 不能只实现解析器和 Worker handler，必须同时打通 Java 业务后端触发 AI 解析任务的入队契约。否则 `/documents/{document_version_id}/parse` 仍只会创建缺少业务字段的任务，Worker 无法下载和解析真实文件。

`parse_document` 任务的最小 payload：

```json
{
  "knowledge_base_version_id": 1001,
  "course_id": 10,
  "document_id": 2001,
  "document_version_id": 3001,
  "object_name": "kb-docs/course-10/document-2001/v3001.pdf",
  "file_ext": ".pdf",
  "checksum_md5": "optional-md5"
}
```

约束：

- `knowledge_base_version_id` 必须由 Java 侧传入并写入 `kb_build_task.knowledge_base_version_id`，禁止继续使用 `0` 占位。
- `document_id`、`document_version_id`、`object_name` 为必填字段；`file_ext` 可由 `object_name` 推断，但 Java 侧传入时以 payload 为准。
- `checksum_md5` 可选；传入时 AI 服务下载后必须校验。
- 保留 Markdown 直传能力仅作为本地/测试入口：当 payload 含 `markdown_content` 且没有 `object_name` 时，走现有 Markdown 解析路径，避免早期联调被 MinIO 阻塞。
- Phase 1 的验收必须包含 API 入队测试和 Worker 执行测试，不能只测 parser。

### 任务清单

#### 1.1 添加解析依赖

- 在 `pyproject.toml` 添加: `pypdf>=5`, `python-pptx>=1`, `python-docx>=1`, `openpyxl>=3`
- 执行 `uv sync` 验证安装

**验收标准**: `uv sync` 成功，import 无报错

#### 1.2 实现 PDF 解析器

- 新建 `app/services/parsing/pdf_parser.py`
- 使用 pypdf 逐页提取文本、尝试提取标题
- 扫描版 PDF → 抛 `AppError(code="PARSE_UNSUPPORTED", http_status=400)`，引导用户上传文字版
- 异常情况: 加密 PDF → `PARSE_ENCRYPTED`; 损坏文件 → `PARSE_CORRUPTED`

**验收标准**: 文字版 PDF 返回 `list[DocumentPage]`；扫描版返回 400 + `PARSE_UNSUPPORTED`

#### 1.3 实现 PPTX 解析器

- 新建 `app/services/parsing/pptx_parser.py`
- 使用 python-pptx 逐 slide 提取: slide title → page title，正文文本 → text
- notes 页可选；图表/图片跳过（留 metadata 占位）

**验收标准**: 含标题/正文的 PPTX 正确映射到 DocumentPage；无标题 slide 以"第 N 页"为标题

#### 1.4 实现 DOCX 解析器

- 新建 `app/services/parsing/docx_parser.py`
- 使用 python-docx 迭代段落
- Heading 1 → 新 page 开始；Heading 2+ → 合并入当前 page
- 表格 → JSON 保留在 `tables_json`

**验收标准**: 含多级标题的 DOCX 按 H1 正确分页；表格内容在 `tables_json` 可查

#### 1.5 实现 XLSX 解析器

- 新建 `app/services/parsing/xlsx_parser.py`
- 使用 openpyxl 按 sheet 遍历
- 每 sheet 转为 Markdown 表格格式文本，作为一个 page
- sheet 名称作为 page title

**验收标准**: 多 sheet XLSX → 每个 sheet 一个 DocumentPage；内容为 Markdown 表格

#### 1.6 实现文件下载器

- 新建 `app/services/parsing/file_downloader.py`
- 从 MinIO 下载文件到临时目录 (`tempfile.mkdtemp`)；文件由 RuoYi（Java 业务后端）上传到 MinIO，AI 服务仅读取
- 超时控制（默认 30s）→ `FILE_DOWNLOAD_TIMEOUT`
- MD5 校验（配置可选）→ `FILE_CHECKSUM_MISMATCH`
- 下载完成后返回本地路径，调用方使用后用 `try/finally` 清理临时文件

**验收标准**: 文件下载成功且校验一致；超时抛指定错误码

#### 1.7 格式检测和分发

- 新建 `app/services/parsing/dispatcher.py`
- 统一入口 `async def parse_file(file_path: str, ext: str, document_id: int, document_version_id: int) -> list[DocumentPage]`
- 根据 `ext` (.pdf/.pptx/.docx/.xlsx/.md) 路由到对应解析器
- 传入 `parse_document_task` handler 也改为走此入口

**验收标准**: 各格式路由正确；未支持格式抛 `PARSE_UNSUPPORTED_FORMAT` (400)

#### 1.8 统一超时/重试装饰器

- 新建 `app/services/parsing/retry.py`
- `@parse_retry` 装饰器: 对 MinIO 网络错误 (`ConnectionError`, `TimeoutError`) 重试 3 次 (1s → 4s → 15s 间隔)
- 对解析器本身加 `asyncio.timeout(120)`，超时抛 `PARSE_TIMEOUT`
- 非可重试异常（格式不支持、文件损坏）直接抛出不重试

**验收标准**: MinIO 网络抖动自动恢复；解析超时返回 `PARSE_TIMEOUT`

#### 1.9 更新 Worker handler

- 修改 `handlers.py` 中 `parse_document_task`：
  - 支持 MinIO 文件路径 (`object_name`) + `file_ext` + `checksum_md5`
  - 保留 `markdown_content` 作为测试/本地兜底路径
  - MinIO 路径调用文件下载器 → 格式分发 → 解析 → 入库
  - 清理临时文件
- 修改 `documents.py` 中 `parse_document`：
  - 接收完整任务请求体，而不是只接收 path 参数
  - 将 `knowledge_base_version_id` 写入 `kb_build_task.knowledge_base_version_id`
  - 将其余字段写入 `payload_json`

**验收标准**: API 入队 payload 完整；Worker 处理 MinIO 任务时完整走下载→解析→入库链路；Markdown 直传测试路径仍可运行

#### 1.10 测试

- 各解析器单元测试（Mock 文件内容）
- 格式检测分发测试
- 超时/重试装饰器测试
- MinIO 下载集成测试（需 MinIO mock）
- coverage ≥ 80%，全部通过

---

## 4. 阶段 2: 知识库构建管道健壮化

### 目标

Worker 管道补充并发控制、增量更新、任务重试、进度可观测性和 chunk 策略配置化。

### 任务清单

#### 2.1 Chunk 策略配置化

- 修改 `chunking/__init__.py` 入口，从 `ChunkStrategyRepo` 读取 `strategy_code + strategy_version`
- 按 `knowledge_base_version_id` 选择对应策略（或使用默认策略）
- 支持 `chunk_method`: `title`, `fixed_size`, `semantic`

**验收标准**: 不同策略配置产生不同 chunk；配置变更后重新构建即生效

#### 2.2 新增 Chunk 策略: semantic

- 新建 `chunking/semantic.py`（或在 `__init__.py` 中扩充）
- 基于 Markdown 段落/列表/代码块边界切分
- 段落超过 `chunk_size` 时，在最近的自然段落边界截断
- 回退: 无结构文本 → 自动降级为 fixed_size

**验收标准**: 5 段落输入 → 产出 ≥5 个 chunk（段落边界优先）；不会在句子中间截断

#### 2.3 Worker 并发控制

- 同一 `kb_build_task` 的子任务链 (parse→chunk→keyword→embedding) 保持串行（当前已是）
- 不同知识库版本的任务可并行执行
- 使用 Redis `SETNX` 实现 `task_type` 级别互斥锁（如 `lock:build_chunk:{kb_version_id}`），TTL=300s
- 获取锁失败的任务保持 pending，下次轮询再试（不跳过）
- Redis 不可用时降级为无锁模式（允许重复调度，由幂等性保障安全）

**验收标准**: 同时插入 2 个 build_chunk 任务 → 1 个 running，1 个保持 pending

#### 2.4 任务失败重试

- Worker 捕获 `HANDLER_ERROR` 后检查 `task.retry_count < 3`：
  - 第 1 次失败 → retry_count=1，将 task_id 写入 Redis ZSET（key=`retry:tasks`，score=now+5s）
  - 第 2 次失败 → retry_count=2，score=now+30s
  - 第 3 次失败 → retry_count=3，标记 `failed`
- Worker 每次轮询先检查 Redis ZSET 取出到期的 task_id，恢复 status=pending 供抢占
- 非可重试错误 (NOT_IMPLEMENTED / PARSE_UNSUPPORTED) → 直接 failed，不重试

**验收标准**: 解析异常自动重试 3 次 → 最终标记 failed；第 2 次成功 → 任务正常完成

#### 2.5 知识库版本建索引事务化

- `build_knowledge_base_version` 任务链如果中途失败，自动清理已创建的中间记录：
  - 删除已写入的 `embedding_index_version`
  - 删除已写入的 `keyword_index_version`
  - 删除已写入的 `chunk_embedding`
- 清理使用独立 session 执行，避免与主事务冲突

**验收标准**: embedding 步骤失败 → 自动清理该版本 keyword_index 和 embedding_index 记录

#### 2.6 增量更新（按知识库版本快照）

- 增量更新不在当前线上 `knowledge_base_version` 内原地修改 chunk。
- Java 侧为本次更新创建新的 `knowledge_base_version`，AI 服务只负责在新版本内解析新文档、构建 chunk、构建 keyword/embedding index。
- 当前 published 版本继续服务；新版本构建完成并通过验收后，由 Java 侧切换 `current_version_id`。
- 如果要复用未变更文档的 chunk，可在新版本构建阶段复制旧版本 chunk 并重建索引，但复制行为必须绑定新 `knowledge_base_version_id`。
- 旧版本 chunk 不做 `status=expired` 原地修改，避免破坏历史检索日志、评估结果和回滚能力。

**验收标准**: 更新文档 A → 生成新的 knowledge_base_version；旧 published 版本仍可检索；新版本验证通过后可由 Java 侧发布切换；回滚时仍可回到旧版本

#### 2.7 管道进度可观测性

- Worker 在每步关键节点上报 `current_step` 和 `progress`
- 在 `pyproject.toml` 添加依赖 `prometheus-client>=0.21`；新增 `app/core/metrics.py` 定义指标：
  - `kb_build_tasks_total{status}` — 任务总数
  - `kb_build_tasks_running` — 运行中
  - `kb_build_task_duration_seconds` — 任务耗时 histogram
  - `kb_build_tasks_failed_total{error_code}` — 按错误码分类
- 在 FastAPI 挂载 `/metrics` 端点

**验收标准**: `GET /internal/v1/kb-tasks/{id}` 返回准确进度；`/metrics` 包含上述指标

#### 2.8 管道 API 增强

- 新增 `GET /internal/v1/kb-tasks` 批量查询，支持分页和 kb_version_id 过滤
- 返回: `Page[KbTaskSummary]` 含 id, type, status, progress, created_at, finished_at

**验收标准**: `GET /internal/v1/kb-tasks?kb_version_id=1&page=1&size=10` 返回正确分页结果

#### 2.9 测试

- Worker 并发测试（Mock Redis + 同时插入 N 个任务）
- 重试逻辑测试（3 次覆盖）
- 新 knowledge_base_version 快照构建与回滚边界验证
- 管道原子性测试（模拟中间失败）
- Chunk 策略配置化测试

---

## 5. 阶段 3: 检索与 RAG 增强

### 目标

补齐 SSE 流式问答、多轮对话上下文、引用校验、检索降级、MMR 多样性和 prompt 配置化。

### 任务清单

#### 3.1 SSE 流式问答

- 实现 `/qa/answer/stream`：使用 `StreamingResponse(media_type="text/event-stream")`
- 数据流: 改写 → 检索（同步）→ LLM 流式 → 逐 token 推送 `data: {...}\n\n` 事件
- 最后推送 sources 对象和 `[DONE]` 标记
- 异常时推送 `data: {"error": "..."}\n\n`（不关闭连接直到 DONE）

**验收标准**: EventSource 收到逐 token 响应；结束事件携带完整 sources 和 log_ref

#### 3.2 查询改写增强

- 同义词扩展: 加载内置同义词词典 (`app/services/retrieval/synonyms.json`，JSON 键值对格式如 `{"ML": ["机器学习"]}`)，启动时缓存到内存
- 中英文检测: 检测输入是纯中文 / 纯英文 / 中英混合
  - 纯中文 → jieba 分词 + 同义词扩展
  - 纯英文 → 空格分词 + 小写归一化
  - 混合 → 双语分词

**验收标准**: "ML 算法" → keyword_query 含"机器学习 算法"(假设同义词表有 ML→机器学习)

#### 3.3 多轮对话上下文

- 读取历史 `qa_retrieval_log` 按 `message_id` 倒序取最近 3 轮
- 将前轮 Q&A 拼入 prompt 的对话历史区域：
  ```
  历史对话：
  用户: 什么是监督学习？
  助手: 监督学习是...
  ---
  用户: 它和无监督学习有什么区别？
  ```
- 合并检索结果: 历史轮次的检索结果不拼入当前 prompt（仅当前轮结果）

**验收标准**: 第 2 轮问"它是什么"→ 准确指向前文的"监督学习"

#### 3.4 引用来源校验

- LLM 返回后解析 `[来源:N]` 标记
- 验证每个 N 都在当前检索的 chunks 范围内 (≤ len(fused))
- 有效引用 → 在 sources 中标注 `source_index=N`
- 无效引用 → 从答案中移除该标记，在 sources 中添加 `invalid=true`
- 检查是否引用了分数 < 0.2 的低质量 chunk → 标记 `WEAK_CITATION`

**验收标准**: `[来源:1]` 能回溯到 chunk_id；无效引用在 sources 中标记且从答案文本移除

#### 3.5 检索降级策略

- `hybrid_retrieve` 增加降级包裹：
  1. 正常: Embedding + 关键词并行检索 → 混合融合
  2. Embedding 异常/超时 → 纯关键词检索
  3. 关键词也异常 → 空结果 + `RETRIEVAL_EMPTY`
- 降级链路写入 `qa_retrieval_log.retrieval_channel = "keyword_only"` 或 `"empty"`

**验收标准**: Embedding 服务中断 → /qa/answer 返回纯关键词结果不是 500

#### 3.6 检索结果多样性（MMR）

- 实现 MMR 算法: 在融合后的结果中迭代选择
  - 每轮选一个 chunk：兼顾与查询的相关性（高 score）和与已选集的最大差异（低与已选最高相似度）
  - `lambda` 参数控制多样性强度（默认 0.5），从 `RetrievalStrategyConfig.rerank_enabled` 控制开关
- 相似度计算：在 `hybrid_retrieve` 返回结果中扩展 `embedding` 字段暂存向量，MMR 阶段做余弦相似度去重
- MMR 在 `RetrievalStrategyConfig.rerank_enabled=true` 时启用，默认 false（向后兼容）

**验收标准**: 10 个同主题 chunk → 只取 1-2 个代表性 chunks，补充其他主题内容

#### 3.7 RAG prompt 配置化

- `qa_answer` 函数改为从 `PromptTemplateRepo.get_by_scenario("qa")` 加载 prompt
- 支持 `prompt_version` 参数（从 request 传入），空则取最新 enabled 版本
- 内置默认 prompt（当前硬编码的 system message）作为兜底
- LLM 调用的 `temperature` 也改为可从 prompt 模板的配置中读取

**验收标准**: 新增一条 `scenario='qa'` 的 prompt 并设为 enabled → 问答立即使用新 prompt

#### 3.8 测试

- SSE 流式集成测试（Mock LLM stream）
- 降级场景 3 条路径（正常/embedding 降级/全部降级）
- 多轮上下文拼接测试
- 引用校验覆盖（有效/无效/空/弱引用）
- MMR 多样性验证（输入 N 个相似结果 → 输出去重后分布）

---

## 6. 阶段 4: 出题/诊断/评分

### 目标

实现完整的 AI 出题、错题诊断和简答评分，含 prompt 模板接入和 schema 校验。

### 任务清单

#### 4.1 Prompt 模板接入

- `generate_questions` / `diagnose` / `grade_short_answer` 统一改为从 `PromptTemplateRepo` 加载 prompt
- 使用 `output_schema` 字段作为 `response_format` 传入 LLM（OpenAI `response_format={type:'json_object'}`）
- 模板缺失时使用内置默认 prompt

**验收标准**: 模板存在 → 使用模板内容；不存在 → 自动使用默认

#### 4.2 AI 出题实现

- `generate_questions` 完整实现：
  1. 根据 `knowledge_point_id` 检索相关 chunk
  2. 组装 prompt（含知识点/难度/题型/数量等参数）
  3. 调用 LLM，指定 `response_format={type:'json_object'}`
  4. 校验返回 JSON 是否符合 `output_schema`
  5. 返回 `list[QuestionDraft]`

**验收标准**: "机器学习"知识点生成 5 道选择题，格式严格符合 schema；chunk 为空时返回 `KNOWLEDGE_POINT_EMPTY`

#### 4.3 出题 Schema 设计

在 `app/schemas/qa.py` 定义：

```python
class QuestionDraft(BaseModel):
    type: Literal["choice", "fill", "true_false", "short_answer"]
    question: str
    options: list[str] | None = None       # choice 时必填
    answer: str                            # 标准答案
    explanation: str                       # 解析
    difficulty: Literal["easy","medium","hard"]
    knowledge_point_id: int | None = None
```

- LLM 返回 JSON 后校验：必填字段缺失 → 重试 1 次；仍缺失 → `SCHEMA_INVALID`

**验收标准**: 每种题型产出不同 schema；必填字段缺失时降级标记

#### 4.4 错题诊断实现

- `diagnose` 改为接收请求体 `DiagnoseRequest`（由 Java 侧传入完整 DTO，避免跨 schema 查库）：
  ```python
  class DiagnoseRequest(BaseModel):
      question: str
      student_answer: str
      correct_answer: str
      knowledge_point_id: int | None = None
      course_id: int
  ```
  1. 根据 `knowledge_point_id` + `course_id` 检索相关 chunk
  2. LLM 分析错因分类（知识盲区/概念混淆/理解偏差/粗心大意）
  3. 返回诊断结果 + 推荐复习的 chunk 引用列表

**验收标准**: 输入"混淆了 MSE 和 MAE" → 诊断结果指出"概念混淆" + chunk 引用

#### 4.5 简答评分完善

- `grade_short_answer` 升级输出为结构化 JSON:

```python
class GradeResult(BaseModel):
    score: int                               # 0-100
    dimensions: dict[str, int]               # 各维度: {完整性, 准确性, 逻辑性}
    reason: str                              # 总体评语
    highlight: str | None = None             # 优秀/待改进句子摘录
```

- 评分标准: 标准答案回传 score=100；完全无关回答 score=0

**验收标准**: 3 个不同质量回答产生有区分度的分数；标准答案稳定 100

#### 4.6 生成 API 参数化

- 路由参数校验:
  - `count`: 1-20，默认 5
  - `difficulty`: `easy | medium | hard`
  - `question_types`: `choice | fill | true_false | short_answer`
- 参数错误返回 422 + 标准错误体

**验收标准**: count=0 返回 422；非法枚举值返回 422

#### 4.7 测试

- 出题函数单元测试（Mock LLM 返回合法/非法 JSON）
- Schema 校验测试（格式错误 LLM 返回的降级路径）
- 诊断函数测试（Mock 检索 + LLM）
- 评分函数测试（区分度验证）
- 参数校验测试

---

## 7. 阶段 5: RAG 离线评估

### 目标

实现完整的评估 runner 和指标计算，使团队能量化追踪检索和 RAG 质量。

### 任务清单

#### 5.1 评估 runner 实现

- 实现 `run_evaluation` 函数：
  1. 读数据集所有 case（`RagEvalCaseRepo.list_by_dataset`）
  2. 对每个 case 依次执行: query_rewrite → hybrid_retrieve → qa_answer
  3. 将结果写入 `RagEvalResult`
  4. 全部完成后标记 run status=completed
  5. 中间失败: 单个 case 失败不影响其他 case（记录 failure_reason 后继续）

**验收标准**: 10 个 case → 10 条 result；中间 case 失败不影响后续

#### 5.2 检索指标计算

在 `RagEvalResult` 中填充以下字段：

| 指标 | 计算方式 | 字段 |
|------|---------|------|
| hit_document | top-k 中是否包含 `expected_sources` 内的文档 | `hit_document` |
| hit_page | 是否命中预期页码 | `hit_page` |
| hit_knowledge_point | top-k 中是否包含 `expected_knowledge_point_id` 相关 chunk | `hit_knowledge_point` |
| recall@k | 预期相关 chunk 在 top-k 中的比例 | `recall_at_k` |
| MRR | 第一个相关 chunk 排位的倒数 | `mrr` |

**验收标准**: 已知 case 的指标手工计算验证一致

#### 5.3 问答指标计算

| 指标 | 计算方式 | 字段 |
|------|---------|------|
| answer_correct | LLM-as-judge: 比较 LLM 回答和 `standard_answer` 的语义等价性 | `answer_correct` |
| citation_correct | LLM 引用的 sources 是否在 `expected_sources` 内 | `citation_correct` |
| reject_correct | 对 `allow_reject=true` 的 case，LLM 是否正确拒答 | `reject_correct` |

- `answer_correct` 使用独立 LLM 调用做评判（不复用回答 LLM）

**验收标准**: 明确可回答的 case → answer_correct=true；应拒答的 → reject_correct=true

#### 5.4 评估报告生成

- 汇总一次 run 的报告（增加一个 Alembic 迁移，在 `rag_eval_run` 表加 `report_json JSONB` 列存储报告）:
  - 基本信息: run_id, dataset_id, kb_version_id, date
  - 检索指标: 平均 recall@k, 平均 MRR, hit_rate
  - 问答指标: answer_correct 率, citation_correct 率, reject 准确率
  - 失败列表: 所有 failure_reason 不为空的 case

**验收标准**: 报告包含上述所有统计，数字与逐条累加一致

#### 5.5 评估 API 完善

| 端点 | 功能 |
|------|------|
| `GET /eval/datasets` | 数据集列表 |
| `GET /eval/datasets/{id}/cases?page=1` | 数据集的所有 case |
| `GET /eval/runs/{id}/results?page=1` | 运行结果明细 |
| `GET /eval/runs/compare?id1=1&id2=2` | 两个 run 的指标对比 |

**验收标准**: 所有端点返回正确分页和对比数据

#### 5.6 测试

- Runner 集成测试（Mock 检索 + LLM）
- 各指标计算单元测试（已知数据验证数值）
- 报告生成测试
- API 端点测试

---

## 8. 阶段间依赖关系

```
Phase 1 (文档解析)
  └── Phase 2 (管道健壮化)
        ├── Phase 3 (检索+RAG)
        │     ├── Phase 4 (出题/诊断)
        │     └── Phase 5 (离线评估)
        └── 每阶段内嵌测试验证
```

- Phase 1 可独立上线（文档解析能力）
- Phase 2 依赖 Phase 1 产生的 DocumentPage
- Phase 3 依赖 Phase 2 产生的索引
- Phase 4 依赖 Phase 3 的检索能力
- Phase 5 依赖 Phase 2 + Phase 3

## 9. 健壮性横切关注点

每个阶段内嵌以下健壮性机制，不另设阶段：

| 维度 | 实现方式 | 覆盖阶段 |
|------|---------|---------|
| 超时控制 | `asyncio.timeout` + MinIO 客户端超时 | 1, 2, 3 |
| 自动重试 | 指数退避重试装饰器 (1s→4s→15s, 上限 3 次) | 1, 2, 3, 4 |
| 降级 | 检索降级 (vector→keyword→empty) | 3 |
| 事务清理 | 管道失败自动回滚中间产物 | 2 |
| 并发控制 | Redis SETNX 互斥锁 + FOR UPDATE SKIP LOCKED | 2 |
| 错误码标准化 | `AppError(code, http_status, detail)` | 1, 2, 3, 4, 5 |
| 可观测性 | Prometheus 指标 + 结构化日志 + 进度字段 | 2, 3 |
| 校验 | Pydantic + JSON Schema + LLM output_schema | 3, 4 |

## 10. 附录

### A. 文件变更清单

```
新增:
  app/services/parsing/pdf_parser.py
  app/services/parsing/pptx_parser.py
  app/services/parsing/docx_parser.py
  app/services/parsing/xlsx_parser.py
  app/services/parsing/file_downloader.py
  app/services/parsing/dispatcher.py
  app/services/parsing/retry.py
  app/services/chunking/semantic.py
  app/core/metrics.py

修改:
  app/api/internal/v1/documents.py       # Phase 1 入队契约
  app/services/parsing/__init__.py       # 集成新解析器
  app/services/chunking/__init__.py      # 配置化 + semantic 策略
  app/services/retrieval/__init__.py     # 降级 + MMR + 改写增强
  app/services/rag/__init__.py           # SSE + 多轮 + prompt 配置化 + 引用校验
  app/services/generation/__init__.py    # 出题/诊断/评分实现
  app/services/eval/__init__.py          # runner 实现
  app/workers/handlers.py                # 重试 + 并发 + 原子化
  app/workers/worker.py                  # 轮询逻辑增强
  app/api/internal/v1/qa.py             # SSE 流式端点
  app/api/internal/v1/kb_tasks.py        # 批量查询
  app/api/internal/v1/questions.py       # 参数校验
  app/api/internal/v1/eval.py            # 补充端点
  app/schemas/qa.py                      # 题型 schema
  pyproject.toml                         # 新增依赖
```

### B. 错误码规约

所有错误码遵循 `{模块}_{异常}` 格式：

| 错误码 | HTTP | 场景 |
|--------|------|------|
| `PARSE_UNSUPPORTED` | 400 | 不支持的文件格式/扫描版 PDF |
| `PARSE_ENCRYPTED` | 400 | PDF 加密 |
| `PARSE_CORRUPTED` | 400 | 文件损坏 |
| `PARSE_TIMEOUT` | 504 | 解析超时 |
| `FILE_DOWNLOAD_TIMEOUT` | 504 | 文件下载超时 |
| `FILE_CHECKSUM_MISMATCH` | 400 | 文件校验失败 |
| `KNOWLEDGE_POINT_EMPTY` | 404 | 知识点无内容 |
| `RETRIEVAL_EMPTY` | 404 | 检索无结果 |
| `SCHEMA_INVALID` | 422 | LLM 输出格式不合法 |
| `TASK_CONCURRENT_LIMIT` | 409 | 并发限制 |

### C. 测试策略

- **单元测试**: 纯函数（指标计算、schema 校验、fusion、MMR）→ `pytest` 直接跑，不 Mock
- **集成测试**: API 端点 + Worker handler → Mock 外部依赖（MinIO/LLM/Embedding），模拟真实数据流
- **边界测试**: 空输入、超大输入、并发竞争、超时模拟、异常 LLM 返回
- **覆盖目标**: 每阶段新增代码覆盖率 ≥ 80%
