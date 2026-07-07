# AI 服务（Python FastAPI）技术设计

> 配套文档：《企业级知识助教系统落地方案》。本文聚焦三件套中缺失的 Python AI 服务，给出它与 RuoYi（Spring Boot）业务后端、RuoYi-Vue3 前端协作的工程化设计。术语（`knowledge_base_version`、`kb_build_task`、`qa_retrieval_log` 等）沿用落地方案。

---

## 1. 服务定位与边界

落地方案 §5.4 已定调分层：**业务系统负责用户、课程、权限、记录、报表；AI 服务负责解析、切片、检索、生成、评估**。本设计严格遵守这一边界。

| 能力 | 归属 | 说明 |
| --- | --- | --- |
| 登录、JWT、RBAC、课程/班级授权 | RuoYi（Java） | AI 服务**不重复实现**权限 |
| 课程/章节/知识点 CRUD、知识库版本状态机与发布 | RuoYi（Java） | 业务流程与审核归业务侧 |
| 题库审核流、试卷、作答、掌握度、看板、审计 | RuoYi（Java） | 业务记录归业务侧 |
| 文档解析、知识结构化、Chunk、Embedding、索引构建 | **FastAPI** | 重 CPU/IO 的 AI 流水线 |
| 查询改写、混合检索、Rerank、Prompt 组装、LLM 生成、引用校验 | **FastAPI** | RAG 核心 |
| AI 出题草稿、错题诊断、简答评分 | **FastAPI** | 仅产出草稿/建议，落库与审核归 Java |
| RAG 离线评估 | **FastAPI** | 评估运行与指标计算 |
| 检索日志、模型调用日志 | **FastAPI 写入** | Java 侧只读用于看板 |

**一句话边界**：FastAPI 是一个**内部 AI 计算服务**，不直接面向终端用户、不做权限决策；它信任由 Java 传入的、已解析好的用户与课程范围上下文。

---

## 2. 集成拓扑（关键决策）

### 2.1 推荐方案 A：Java 作为唯一网关（BFF），FastAPI 为内网服务

```text
RuoYi-Vue3 (浏览器)
   │  Authorization: Bearer <ruoyi-jwt>
   ▼
Nginx ──/prod-api──► RuoYi 业务后端 (8080)
                        │ 1) 校验 JWT + Redis 取 LoginUser
                        │ 2) RBAC / 课程授权过滤（course_user + class_user+class_course）
                        │ 3) 解析出 user_id、可访问 course_ids、kb_version_id
                        │ 4) 内网调用，带 X-Internal-Token + 已解析上下文
                        ▼
                  FastAPI AI 服务 (8000, 仅内网)
                        ├─ PostgreSQL (共享实例, AI 自有表)
                        ├─ Redis (任务/缓存)
                        ├─ 向量库 (pgvector / Qdrant)
                        ├─ MinIO (原始资料/Markdown)
                        └─ 模型网关 (OpenAI 兼容: LLM + Embedding + Rerank)
```

**理由**：
- 与落地方案分层一致；权限只在 Java 实现一份，避免 FastAPI 重写课程授权 SQL。
- FastAPI 不必解析 RuoYi 存在 Redis 里的 `LoginUser`（RuoYi 用 FastJSON2 序列化、带 `@class` 类型信息，跨语言反序列化很脏）。
- 内网隔离 + 共享密钥即可保证调用安全，无需 FastAPI 自建用户体系。

**内部鉴权**：FastAPI 校验 `X-Internal-Token`（与 Java 共享的强随机密钥，HMAC 或固定 Bearer），并限制监听地址/安全组只对业务后端开放。生产可升级为 mTLS。

### 2.2 流式问答的处理

问答需要 SSE/流式输出。两种做法：
1. **Java 反向代理 SSE**（推荐）：前端连 Java，Java 以流式把 FastAPI 的 SSE 透传出去，鉴权仍在 Java。
2. **前端直连 FastAPI 的流式端点**：此时 FastAPI 必须做**纵深防御**——校验 RuoYi JWT（HS512，secret `abcdefghijklmnopqrstuvwxyz`，claim `login_user_key`）并回查 Redis。仅当方案 1 的代理延迟不可接受时启用，且课程范围仍需由 Java 预先签发短期票据传入。

> 决策点：默认采用方案 A + SSE 由 Java 透传。若团队希望前端直连 AI 流式接口，请告知，我再补充 FastAPI 端的 RuoYi-JWT 校验与短期票据设计。

---

## 3. 数据所有权与存储

### 3.1 共享一个 PostgreSQL 实例，按表划分所有权

复用 RuoYi 的 PostgreSQL（库 `ruoyi` 或新建库 `kb_ai`，推荐**同实例独立 schema `ai`**，避免与 `sys_*` 混在一起）。

| 表（落地方案 §10.1） | 写入方 | 读取方 |
| --- | --- | --- |
| `sys_*`, `org`, `department`, `user/role`, `class_*`, `course_user` | Java | Java |
| `course`, `course_chapter`, `knowledge_point` | Java | Java + **FastAPI(只读)** |
| `knowledge_base`, `knowledge_base_version` | Java（状态机/发布） | Java + **FastAPI(只读当前发布版)** |
| `document`, `document_version`, `knowledge_base_version_document` | Java 建记录 + **FastAPI 改 status** | 双方 |
| `document_page`, `knowledge_chunk`, `chunk_strategy` | **FastAPI** | 双方 |
| `embedding_index_version`, `keyword_index_version`, `retrieval_strategy_config` | **FastAPI** | 双方 |
| `prompt_template` | **FastAPI**（阶段 4 可 Java 管理） | FastAPI |
| `kb_build_task` | **FastAPI**（Java 可创建/触发） | 双方 |
| `qa_session`, `qa_message`, `qa_feedback` | Java | 双方 |
| `qa_retrieval_log`, `model_call_log` | **FastAPI** | Java(看板只读) |
| `rag_eval_*` | **FastAPI** | 双方 |
| `question`, `question_option`, `exam_*`, `answer_record`, `wrong_answer`, `student_knowledge_mastery`, `review_record`, `audit_log` | Java | Java |

原则：**谁的核心流水线产物，谁建表谁写**。AI 流水线表（chunk/index/log/eval）由 FastAPI 用 Alembic 管理迁移，放 `ai` schema；业务表由 RuoYi 的 SQL 脚本管理。双方对共享只读表不写。

### 3.2 向量库

- **MVP：pgvector**（复用现有 PostgreSQL，运维最简，落地方案允许）。
- **生产：Qdrant / Milvus**（多课程、大数据量、高并发）。
- 代码层用 `VectorStore` 抽象接口隔离，切换不改业务代码。`embedding_index_version.vector_store` 与 `collection_name` 记录实际归属，支持换模型/换库后的可追溯（§10.2）。

### 3.3 中文全文检索（重要工程细节）

落地方案选 PostgreSQL 全文检索做关键词召回，但 **PG 默认不分中文词**。方案：
- 用 **jieba** 预分词，把结果写入 `knowledge_chunk` 的 `tsv tsvector` 列（`to_tsvector('simple', 分词结果)`），查询时同样用 jieba 分词后 `plainto_tsquery`。
- 或安装 **zhparser** 扩展（需 DBA 配合）。MVP 推荐 jieba 预分词路线，零扩展依赖、可控。
- 关键词分数取 `ts_rank`，与向量分数一起进入加权排序并写入 `qa_retrieval_log`。

### 3.4 对象存储

MinIO（S3 兼容）。存原始资料、解析后的 Markdown 中间层、附件。`document_version.file_path` 存对象 key。

---

## 4. 技术栈

| 类别 | 选型 | 说明 |
| --- | --- | --- |
| 语言/运行时 | Python 3.11+ | |
| Web 框架 | FastAPI + Uvicorn（Gunicorn 多 worker） | 异步、自带 OpenAPI |
| 配置 | pydantic-settings | 全部从环境变量注入 |
| 校验/序列化 | Pydantic v2 | 请求/响应/LLM 输出 schema |
| ORM/DB | SQLAlchemy 2.0 (async) + asyncpg | AI 自有表 |
| 迁移 | Alembic | 仅管理 `ai` schema |
| 缓存/队列 | redis-py (async) | 任务信号、热点配置、限流 |
| HTTP 客户端 | httpx (async) | 调模型网关 |
| 向量库 | pgvector(MVP) / qdrant-client(prod) | `VectorStore` 抽象 |
| 文档解析 | python-pptx, pypdf/pdfplumber, python-docx, openpyxl, markdown, beautifulsoup4 | 阶段 4 可引入 unstructured/MinerU |
| 中文分词 | jieba | 全文检索 + 关键词召回 |
| LLM/Embedding | openai SDK 指向 OpenAI 兼容网关 | 屏蔽厂商差异 |
| Rerank（阶段 4） | BGE-Reranker（网关或本地） | top20~50 精排 |
| 任务执行 | `kb_build_task` 表 + 后台 Worker（可选 arq/Redis 队列） | MVP 同进程，生产独立集群 |
| 对象存储 | minio / boto3 | |
| 日志 | structlog（JSON 结构化） | |
| 指标 | prometheus-fastapi-instrumentator | 阶段 4 接 Prometheus |
| 测试 | pytest + pytest-asyncio + httpx AsyncClient | |
| 质量 | ruff + mypy | |

---

## 5. 工程结构

```text
ai-service/
├─ pyproject.toml
├─ Dockerfile
├─ .env.example
├─ alembic/                      # 仅 ai schema 迁移
├─ app/
│  ├─ main.py                    # FastAPI 实例、路由挂载、生命周期
│  ├─ core/
│  │  ├─ config.py               # pydantic-settings
│  │  ├─ security.py             # X-Internal-Token 校验 (+可选 RuoYi JWT)
│  │  ├─ db.py                   # async engine / session
│  │  ├─ redis.py
│  │  ├─ logging.py
│  │  └─ errors.py               # 统一异常 -> 错误响应
│  ├─ api/internal/v1/
│  │  ├─ documents.py            # 解析触发
│  │  ├─ kb_versions.py          # 构建/重建触发
│  │  ├─ kb_tasks.py             # 任务状态/重试
│  │  ├─ qa.py                   # 同步 + SSE 问答
│  │  ├─ questions.py            # 出题草稿、简答评分、错题诊断
│  │  └─ eval.py                 # 离线评估
│  ├─ schemas/                   # Pydantic DTO（内部契约）
│  ├─ models/                    # SQLAlchemy（ai schema）
│  ├─ repositories/              # DB 访问
│  ├─ services/
│  │  ├─ parsing/                # ppt/pdf/docx/xlsx/md/html -> 标准 page 结构
│  │  ├─ structuring/            # page -> Markdown 中间层 / 知识点(阶段1人工)
│  │  ├─ chunking/               # 策略：title / knowledge_point / semantic / fixed
│  │  ├─ embedding/              # 向量化 + 写向量库/索引版本
│  │  ├─ retrieval/              # query_rewrite, vector, keyword, hybrid, scorer, rerank
│  │  ├─ rag/                    # prompt 组装, 生成, 引用校验, 拒答策略
│  │  ├─ generation/            # 出题、错题诊断、简答评分
│  │  └─ eval/                   # 评估 runner + 指标
│  ├─ gateway/                   # llm_client, embedding_client（OpenAI 兼容）
│  ├─ vectorstore/               # interface + pgvector_impl + qdrant_impl
│  └─ workers/
│     ├─ worker.py               # 轮询 kb_build_task 的后台进程入口
│     └─ pipeline.py             # task_type -> handler 编排
└─ tests/
```

分层依赖方向：`api → services → (repositories / gateway / vectorstore)`，`workers` 复用同一批 `services`。services 不直接碰 FastAPI 的 Request 对象，便于在 Worker 与 API 间复用、便于单测。

---

## 6. 模块设计（对应落地方案 §9 AI 能力）

### 6.1 文档解析 `services/parsing`
- 按扩展名分发 loader，统一输出 §9.1 的标准结构（`document_id/version_id/pages[]`）。
- 每种 loader 实现 `BaseLoader.load(file) -> ParsedDocument`，新增格式只加一个 loader。
- 结果落 `document_page`，Markdown 中间层写 MinIO，`document_version.status` 流转 `parsing→parsed`。

### 6.2 知识结构化 `services/structuring`
- 阶段 1：仅产出可审核的 Markdown 中间层；章节/知识点为 **Java 侧人工维护**（落地方案 §12.1 明确阶段 1 不做自动识别）。
- 阶段 4：LLM 自动抽取知识点结构作为草稿。

### 6.3 Chunk `services/chunking`
- 策略可插拔：`title`、`knowledge_point`（MVP 主策略：标题层级 + 知识点合并）、`semantic`、`fixed_size`（兜底）。
- 每次构建固定到一个 `chunk_strategy` 版本，chunk 落 `knowledge_chunk`，强制保留 `course_id/chapter_id/knowledge_point_id/document_version_id/page_start/page_end/chunk_strategy_version` 等元数据（§9.3）。
- 写 `chunk_hash` 便于增量与去重。

### 6.4 Embedding `services/embedding` + `gateway/embedding_client`
- 经模型网关向量化，写向量库；登记 `embedding_index_version`（模型名/版本/维度/库/collection）。换模型必须新建索引版本（§10.2），保证评估可对比。

### 6.5 检索 `services/retrieval`（MVP 轻量混合检索，§9.4/§9.5）
```text
query_rewrite ─► { normalized, keyword_query, semantic_query, expanded_terms }
   ├─ vector_search(top 20)        # pgvector / Qdrant
   ├─ keyword_search(top 20)       # PG 全文 + jieba
   ├─ metadata_filter              # 课程/知识库版本/文档状态/语言/资料类型
   ├─ merge + dedup(by chunk_hash)
   └─ weighted_score top 5
      final = vector*Wv + keyword*Wk + metadata*Wm   # 权重来自 retrieval_strategy_config，不写死
```
- 全过程逐条写 `qa_retrieval_log`：`vector_score/keyword_score/metadata_score/final_score/retrieval_channel/matched_terms/used_in_prompt/rank_no`，满足 §21 验收。
- 阶段 4：在 merge 后插入 `rerank` 阶段（BGE-Reranker），写 `rerank_score`。

### 6.6 RAG 生成 `services/rag`
- **拒答策略**（§9.6）：最低分阈值、未命中当前发布版、主题不一致、无可引用证据、超出授权范围 → 返回拒答并写 `reject_reason`。
- Prompt 由 `prompt_template`（按 `scenario` + `prompt_version`）组装，top5 chunk 注入。
- 生成后做**引用校验**与资料外内容检测（§9.8）；失败重试一次→降级→记录。
- 所有 LLM 调用写 `model_call_log`（耗时、token、失败原因，**不记密钥**，§14）。

### 6.7 出题/诊断/评分 `services/generation`
- 出题：检索相关 chunk → LLM 产出题目 JSON → **Pydantic schema 校验** + 选项/答案格式化 → 返回 `ai_draft` 给 Java（Java 落 `question` 走审核流）。带 `source_chunk_id` 便于溯源。
- 错题诊断：按 §8.6 错因分类（`concept_missing` 等）输出建议。
- 简答评分：LLM 辅助评分，返回分数 + 理由给 Java。

### 6.8 评估 `services/eval`（阶段 1 轻量离线评估，§16）
- 输入 `rag_eval_dataset/_case`，固定 `knowledge_base_version`，跑改写→混合检索→生成。
- 计算 Recall@K、MRR、命中知识点/页码准确率、引用准确率、拒答准确率，写 `rag_eval_run/_result`，与上次基线对比并归类失败原因。

---

## 7. 内部 API 契约（Java → FastAPI）

FastAPI 讲自己的干净 REST/JSON（标准 HTTP 状态码 + 统一错误体），**不模仿 AjaxResult**；由 Java 适配成 `AjaxResult/TableDataInfo` 再给前端。所有路径前缀 `/internal/v1`，需 `X-Internal-Token`。

```text
# 解析与构建（异步：入队后返回 task_id）
POST /internal/v1/documents/{documentVersionId}/parse        -> {task_id}
POST /internal/v1/kb-versions/{kbVersionId}/build            -> {task_id}
POST /internal/v1/kb-versions/{kbVersionId}/rebuild          -> {task_id}
GET  /internal/v1/kb-tasks/{taskId}                          -> 任务状态/进度/错误
POST /internal/v1/kb-tasks/{taskId}/retry
POST /internal/v1/kb-tasks/{taskId}/cancel

# 问答（同步或 SSE；上下文由 Java 解析后传入）
POST /internal/v1/qa/answer
     body: { user_id, course_id, kb_version_id, session_id, message_id, question }
     resp: { answer, sources[], reject_reason?, retrieval_log_ref }
POST /internal/v1/qa/answer/stream      # SSE，逐 token，结束补 sources

# 生成类（返回草稿/建议，由 Java 落库）
POST /internal/v1/questions/generate    # body: course/chapter/knowledge_point + 数量/题型
POST /internal/v1/diagnose              # 错题诊断
POST /internal/v1/grade/short-answer    # 简答评分

# 评估
POST /internal/v1/eval/runs             # 触发离线评估
GET  /internal/v1/eval/runs/{runId}
```

> 检索日志/模型日志的查询（落地方案 §11.4 `/api/admin/*`）由 Java 直接读共享表渲染看板，无需经 FastAPI。

错误体：`{ "error": { "code": "RETRIEVAL_EMPTY", "message": "...", "detail": {...} } }`，HTTP 4xx/5xx 语义化；Java 映射到 `AjaxResult.code`。

---

## 8. 任务与 Worker 设计（落地方案 §12.1）

- `kb_build_task` 为任务**事实来源**；`task_type` 覆盖 `parse_document / structure_knowledge / build_chunk / build_embedding_index / build_keyword_index / build_knowledge_base_version / rebuild_knowledge_base_version`。
- Worker（`app/workers/worker.py`）轮询 `pending` 任务（`FOR UPDATE SKIP LOCKED` 抢占），按 `task_type` 路由到 handler，更新 `status/current_step/progress/error_*/retry_count`。
- **MVP**：Worker 可与 API 同镜像、`command` 区分（`uvicorn app.main` vs `python -m app.workers.worker`），甚至同进程起后台任务。**生产**：拆独立 Worker 集群，可换 arq/RabbitMQ。
- **重建不覆盖线上版**（§12.1）：v3 published 持续服务 → 新建 v4 draft/building → 构建成功转 ready → 人工发布切 `current_version_id` → v3 archived 可回滚；v4 失败则 v3 继续服务，管理员看失败任务重试。

完整资料入库流水线（与 §12.1 对齐）：
```text
Java: 建 document/document_version + 上传 MinIO + 建 kb_version(draft) + 绑定快照 + 建 kb_build_task
  └─► FastAPI Worker: parse → Markdown → (人工维护知识点) → chunk → embedding → 写向量库
        → 建 embedding/keyword index version → kb_version=ready
  └─► Java: 人工确认 publish → 切 current_version_id
```

---

## 9. 配置与密钥

`.env`（pydantic-settings 读取）：
```text
APP_ENV=dev
INTERNAL_TOKEN=<与 Java 共享的强随机串>
DATABASE_URL=postgresql+asyncpg://postgres:123456@localhost:5432/ruoyi
DB_SCHEMA=ai
REDIS_URL=redis://localhost:6379/1            # 与 RuoYi(db0) 隔离
MINIO_ENDPOINT=localhost:9000  MINIO_AK=...  MINIO_SK=...  MINIO_BUCKET=kb-docs
VECTOR_STORE=pgvector                          # or qdrant
QDRANT_URL=http://localhost:6333
# LLM 与 Embedding base_url 分离：便于 bge 先私有化、LLM 仍走云 API
LLM_BASE_URL=https://api.vendor.com/v1   LLM_API_KEY=...   LLM_MODEL=...
EMBEDDING_BASE_URL=https://api.bge-host/v1  EMBEDDING_API_KEY=...
EMBEDDING_MODEL=bge-m3   EMBEDDING_DIM=1024
# 可选：仅当前端直连流式端点时才需要
RUOYI_JWT_SECRET=abcdefghijklmnopqrstuvwxyz   RUOYI_JWT_ALG=HS512
```
密钥独立管理；`model_call_log` 不落密钥（§14）。

---

## 10. 部署

### 10.1 MVP（Docker Compose，落地方案 §13.1）
```text
nginx              # /prod-api -> ruoyi:8080；前端静态
ruoyi-admin:8080   # 业务后端（已有）
ai-service:8000    # FastAPI（仅内网）
ai-worker          # 同镜像，跑 worker
postgres:5432      # 共享，含 pgvector 扩展，ai schema
redis:6379
minio:9000
qdrant:6333        # 可选，MVP 用 pgvector 则免
```
AI 服务/Worker 不对公网暴露，只允许业务后端访问。

### 10.2 生产（§13.2）
AI 服务集群 + 独立 Worker 集群 + Qdrant/Milvus + Elasticsearch（升级 BM25）+ Prometheus/Grafana + ELK/Loki；引入 Rerank、Prompt 版本管理、模型网关多厂商、灰度发布。

---

## 11. 可观测性与安全

- **日志**：structlog JSON，贯穿 trace_id；解析/向量化/检索/模型调用/失败各有日志（§15）。
- **指标**：问答成功率、拒答率、平均响应时间、检索命中率、满意率、模型失败率、解析失败率、队列积压（§15 关键指标）。
- **安全底线**（§14）：内部鉴权 + 网络隔离；文件类型校验（Java 上传时 + FastAPI 解析前双校验）；模型日志不记密钥；日志/资料配置保留周期；删除资料时联动清理对象存储、chunk、向量与全文索引。

---

## 12. 与落地方案阶段的对齐（FastAPI 侧阶段 1 范围）

**做（对应 §17 阶段 1 / §21 验收）**：解析任务、Markdown 中间层、Chunk + 策略版本、Embedding + 索引版本、PG 全文索引（jieba）、轻量混合检索、查询改写、RAG 问答 + 引用、拒答 + 原因、检索日志、模型调用日志、`kb_build_task` 与重试、知识库重建、最小离线评估。

**不做（阶段 1 留到阶段 4）**：知识点自动识别、知识结构审核流、独立 Rerank 服务、RAG 评估平台化、Prompt 版本管理后台、多厂商模型自动路由。

---

## 13. 已确认决策

| # | 决策 | 结论 | 要点 |
| --- | --- | --- | --- |
| 1 | 集成拓扑 | **Java 单一网关(BFF) + FastAPI 内网** | 权限只在 Java；FastAPI 信任 `X-Internal-Token` + 已解析上下文；SSE 由 Java 透传 |
| 2 | 数据库 | **同实例同库 `ruoyi` + 独立 schema `ai` + pgvector 扩展** | AI 表放 `ai.`，可跨 schema JOIN 业务表；Alembic 只管 `ai` schema；负载压力大时再整体迁出独立实例 |
| 3 | 向量库 | **MVP pgvector**，`VectorStore` 抽象留 Qdrant 后路 | 数据量（~10万–百万向量）pgvector 足够；元数据过滤用 SQL 最省事 |
| 4 | 模型 | **OpenAI 兼容网关**；Embedding=bge-m3(dim 1024)、LLM=云 API | `EMBEDDING_BASE_URL` 与 `LLM_BASE_URL` **分离**，便于 bge 先私有化、LLM 仍走 API；后期私有化只改 base_url；换模型必登记 `embedding_index_version` |
| 5 | Worker | **`kb_build_task` 数据库轮询 + 独立进程**（同镜像） | `FOR UPDATE SKIP LOCKED` 抢占；Redis 仅缓存/信号；多课程高并发期再升级 arq/RabbitMQ |

下一步：进入实现规划（脚手架、Alembic 初始迁移、最小问答闭环）。
