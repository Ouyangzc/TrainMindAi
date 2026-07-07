# AI 服务表结构设计（PostgreSQL `ai` schema）

> 配套《AI 服务技术设计（FastAPI）》。本文细化 **FastAPI 自有、由 Alembic 管理**的表，全部建在 `ai` schema；业务表（`course`/`knowledge_point`/`knowledge_base*`/`document*` 等）由 RuoYi 管理在 `public`，本文只列其被引用的主键作 FK 参照。落地方案 §10 的字段名原样保留，并补齐类型、主外键、索引与约束。

---

## 0. 约定与初始化

**命名/类型约定**
- 主键：`bigserial`（与 RuoYi PostgreSQL 一致）。
- 时间：`timestamptz`，默认 `now()`（比 RuoYi 的无时区 `timestamp` 更正确，跨时区日志不会错）。
- 枚举类状态：用 `varchar` + `CHECK`（避免 PG `enum` 后续加值要 `ALTER TYPE` 的痛）。
- 结构化元数据：`jsonb`（`metadata_json`/`output_schema`/`expected_sources`）。
- 向量：`vector(1024)`（bge-m3 维度；换模型见 §3 索引版本）。
- 全文：`tsvector`，由应用层 jieba 预分词后 `to_tsvector('simple', 分词文本)` 写入。

**跨 schema 外键（已确认：松耦合）**：所有指向 `public` 业务表的列（DDL 中 `-- [XREF]` 标注）一律为**带索引的普通 `bigint` 列，不建跨 schema 外键**，引用完整性由应用层保证。这样 Java 与 FastAPI 的迁移完全独立，AI 表无需等 RuoYi 表先建。
- 代价：`public.knowledge_base_version` 等被删除时**不会自动级联**清理 AI 数据；删除/归档由应用层（§14 保留策略）显式处理。
- `ai` schema **内部**的外键仍保留（如 `chunk_embedding → knowledge_chunk`、`rag_eval_* ` 之间），享受 `ON DELETE CASCADE`。

**初始化迁移（0001）**
```sql
CREATE SCHEMA IF NOT EXISTS ai;
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- 可选：模糊匹配/相似度
-- Alembic version_table 也放 ai：alembic_version 配 version_table_schema='ai'
```

**被引用的 public 业务表（RuoYi 管理，仅参照）**
`public.course(id)`、`public.course_chapter(id)`、`public.knowledge_point(id)`、`public.knowledge_base(id)`、`public.knowledge_base_version(id)`、`public.document(id)`、`public.document_version(id)`、`public.qa_session(id)`、`public.qa_message(id)`。

---

## 1. 资料解析产物

### `ai.document_page`
解析后的页内容（落地方案 §10.1）。FastAPI 解析任务写入。
```sql
CREATE TABLE ai.document_page (
    id                   bigserial PRIMARY KEY,
    document_id          bigint NOT NULL,          -- [XREF] public.document(id)
    document_version_id  bigint NOT NULL,          -- [XREF] public.document_version(id)
    page_number          int    NOT NULL,
    title                varchar(512),
    text                 text,
    tables_json          jsonb  DEFAULT '[]',      -- 抽取的表格
    images_json          jsonb  DEFAULT '[]',      -- 图片引用/OCR
    metadata_json        jsonb  DEFAULT '{}',
    created_at           timestamptz NOT NULL DEFAULT now(),
    -- document_id / document_version_id：松耦合普通列（无跨 schema FK），清理由应用层负责
    CONSTRAINT uq_page UNIQUE (document_version_id, page_number)
);
CREATE INDEX idx_page_docver ON ai.document_page(document_version_id);
```

---

## 2. 切片与策略

### `ai.chunk_strategy`
Chunk 策略版本（§10.2）。
```sql
CREATE TABLE ai.chunk_strategy (
    id               bigserial PRIMARY KEY,
    strategy_code    varchar(64)  NOT NULL,
    strategy_version varchar(32)  NOT NULL,
    chunk_method     varchar(32)  NOT NULL
        CHECK (chunk_method IN ('title','knowledge_point','semantic','fixed_size')),
    chunk_size       int,
    chunk_overlap    int,
    merge_rule       varchar(255),
    split_rule       varchar(255),
    metadata_rule    varchar(255),
    enabled          boolean NOT NULL DEFAULT true,
    created_by       bigint,
    created_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_chunk_strategy UNIQUE (strategy_code, strategy_version)
);
```

### `ai.knowledge_chunk`
知识切片（§10.2）。注意：**向量不存这里**（见 §2 `chunk_embedding`），这里只存文本、元数据和全文 `tsv`。
```sql
CREATE TABLE ai.knowledge_chunk (
    id                        bigserial PRIMARY KEY,
    knowledge_base_version_id bigint NOT NULL,     -- [XREF] public.knowledge_base_version(id) 权威关联
    course_id                 bigint NOT NULL,     -- [XREF] public.course(id)
    chapter_id                bigint,              -- [XREF] public.course_chapter(id)
    knowledge_point_id        bigint,              -- [XREF] public.knowledge_point(id)
    document_id               bigint NOT NULL,     -- [XREF] public.document(id)
    document_version_id       bigint NOT NULL,     -- [XREF] public.document_version(id)
    chunk_text                text   NOT NULL,
    source_file               varchar(512),
    page_start                int,
    page_end                  int,
    chunk_hash                varchar(64) NOT NULL,    -- 去重/增量
    chunk_type                varchar(32),             -- knowledge_point / title / ...
    chunk_strategy_version    varchar(32) NOT NULL,    -- 冗余记录本切片所用策略
    metadata_json             jsonb DEFAULT '{}',      -- 见落地方案 §9.3 chunk 元数据
    tsv                       tsvector,                -- jieba 预分词后写入
    status                    varchar(16) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','disabled')),
    created_at                timestamptz NOT NULL DEFAULT now(),
    -- 所有 [XREF] 列为松耦合普通列（无跨 schema FK）；版本删除由应用层级联清理
    CONSTRAINT uq_chunk_hash UNIQUE (knowledge_base_version_id, chunk_hash)
);
CREATE INDEX idx_chunk_kbver  ON ai.knowledge_chunk(knowledge_base_version_id);
CREATE INDEX idx_chunk_kp     ON ai.knowledge_chunk(knowledge_point_id);
CREATE INDEX idx_chunk_doc    ON ai.knowledge_chunk(document_version_id);
CREATE INDEX idx_chunk_tsv    ON ai.knowledge_chunk USING gin(tsv);          -- 全文召回
-- 元数据过滤常用组合
CREATE INDEX idx_chunk_filter ON ai.knowledge_chunk(knowledge_base_version_id, knowledge_point_id, status);
```

### `ai.chunk_embedding`（细化新增表）
**落地方案隐含、本文显式化**：把向量从 `knowledge_chunk` 拆出，按 (chunk, 索引版本) 存。
理由：① 同一批 chunk 可被不同 embedding 模型分别向量化，支撑 §9.5 评估对比（A/B 模型）；② pgvector 的 HNSW 索引要求固定维度，独立表便于管理；③ 不同维度模型并存时按表/列隔离更清晰。
```sql
CREATE TABLE ai.chunk_embedding (
    id                          bigserial PRIMARY KEY,
    chunk_id                    bigint NOT NULL REFERENCES ai.knowledge_chunk(id) ON DELETE CASCADE,
    embedding_index_version_id  bigint NOT NULL REFERENCES ai.embedding_index_version(id) ON DELETE CASCADE,
    embedding                   vector(1024) NOT NULL,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_chunk_emb UNIQUE (chunk_id, embedding_index_version_id)
);
-- 近邻检索（余弦）。HNSW 在 pgvector >=0.5
CREATE INDEX idx_chunk_emb_hnsw ON ai.chunk_embedding
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunk_emb_idxver ON ai.chunk_embedding(embedding_index_version_id);
```
> 注：`chunk_embedding` 引用 `embedding_index_version`，故 0002 迁移里 `embedding_index_version` 须先于本表创建。

---

## 3. 索引版本

### `ai.embedding_index_version`
向量索引版本（§10.2）。换 embedding 模型必新建一行。
```sql
CREATE TABLE ai.embedding_index_version (
    id                        bigserial PRIMARY KEY,
    knowledge_base_version_id bigint NOT NULL,     -- [XREF] public.knowledge_base_version(id)
    embedding_model           varchar(128) NOT NULL,   -- bge-m3
    embedding_model_version   varchar(64)  NOT NULL,
    embedding_dim             int  NOT NULL,           -- 1024
    vector_store              varchar(32)  NOT NULL    -- pgvector / qdrant / milvus
        CHECK (vector_store IN ('pgvector','qdrant','milvus')),
    collection_name           varchar(128),            -- 向量库 collection；pgvector 可空
    chunk_count               int DEFAULT 0,
    status                    varchar(16) NOT NULL DEFAULT 'building'
        CHECK (status IN ('building','ready','failed','archived')),
    created_at                timestamptz NOT NULL DEFAULT now()
    -- knowledge_base_version_id：松耦合普通列（无跨 schema FK）
);
CREATE INDEX idx_embidx_kbver ON ai.embedding_index_version(knowledge_base_version_id);
```

### `ai.keyword_index_version`
全文索引版本（落地方案 §10.1）。MVP 用 PG 全文（jieba），本表记录其元数据；生产迁 ES 时记录 ES 索引名。
```sql
CREATE TABLE ai.keyword_index_version (
    id                        bigserial PRIMARY KEY,
    knowledge_base_version_id bigint NOT NULL,     -- [XREF] public.knowledge_base_version(id)
    index_engine              varchar(32) NOT NULL DEFAULT 'pg_fts'
        CHECK (index_engine IN ('pg_fts','elasticsearch','opensearch')),
    analyzer                  varchar(64),             -- jieba / ik_smart ...
    index_name                varchar(128),            -- ES 索引名；pg_fts 可空
    chunk_count               int DEFAULT 0,
    status                    varchar(16) NOT NULL DEFAULT 'building'
        CHECK (status IN ('building','ready','failed','archived')),
    created_at                timestamptz NOT NULL DEFAULT now()
    -- knowledge_base_version_id：松耦合普通列（无跨 schema FK）
);
CREATE INDEX idx_kwidx_kbver ON ai.keyword_index_version(knowledge_base_version_id);
```

---

## 4. 检索与 Prompt 配置

### `ai.retrieval_strategy_config`
检索策略配置（§10.2）。权重不写死，落库 + 写检索日志。
```sql
CREATE TABLE ai.retrieval_strategy_config (
    id                  bigserial PRIMARY KEY,
    strategy_code       varchar(64) NOT NULL,
    strategy_version    varchar(32) NOT NULL,
    vector_top_k        int NOT NULL DEFAULT 20,
    keyword_top_k       int NOT NULL DEFAULT 20,
    final_top_k         int NOT NULL DEFAULT 5,
    vector_weight       numeric(4,3) NOT NULL DEFAULT 0.600,
    keyword_weight      numeric(4,3) NOT NULL DEFAULT 0.300,
    metadata_weight     numeric(4,3) NOT NULL DEFAULT 0.100,
    min_score_threshold numeric(5,4) NOT NULL DEFAULT 0.0,   -- 拒答阈值
    rerank_enabled      boolean NOT NULL DEFAULT false,      -- 阶段 4
    enabled             boolean NOT NULL DEFAULT true,
    created_by          bigint,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_retr_strategy UNIQUE (strategy_code, strategy_version)
);
```

### `ai.prompt_template`
Prompt 模板版本（§10.2、§9.7）。
```sql
CREATE TABLE ai.prompt_template (
    id             bigserial PRIMARY KEY,
    prompt_code    varchar(64) NOT NULL,
    prompt_version varchar(32) NOT NULL,
    scenario       varchar(32) NOT NULL             -- qa / question_gen / diagnose / reteach / grade / quality_check
        CHECK (scenario IN ('qa','question_gen','diagnose','reteach','grade','quality_check')),
    prompt_content text NOT NULL,
    output_schema  jsonb,                            -- 输出 JSON schema，供 §9.8 校验
    enabled        boolean NOT NULL DEFAULT true,
    created_by     bigint,
    created_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_prompt UNIQUE (prompt_code, prompt_version)
);
CREATE INDEX idx_prompt_scenario ON ai.prompt_template(scenario, enabled);
```

---

## 5. 构建任务

### `ai.kb_build_task`
知识库构建任务（§10.2）。Worker 轮询的事实来源。
```sql
CREATE TABLE ai.kb_build_task (
    id                        bigserial PRIMARY KEY,
    knowledge_base_version_id bigint NOT NULL,     -- [XREF] public.knowledge_base_version(id)
    task_type   varchar(40) NOT NULL CHECK (task_type IN (
        'parse_document','structure_knowledge','build_chunk',
        'build_embedding_index','build_keyword_index',
        'build_knowledge_base_version','rebuild_knowledge_base_version')),
    status      varchar(16) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','running','success','failed','cancelled')),
    current_step  varchar(64),
    progress      int NOT NULL DEFAULT 0,           -- 0..100
    payload_json  jsonb DEFAULT '{}',               -- 任务入参（document_version_ids 等）
    error_code    varchar(64),
    error_message text,
    retry_count   int NOT NULL DEFAULT 0,
    started_at    timestamptz,
    finished_at   timestamptz,
    created_by    bigint,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
    -- knowledge_base_version_id：松耦合普通列（无跨 schema FK）
);
-- Worker 抢占：只扫 pending（部分索引）
CREATE INDEX idx_task_pending ON ai.kb_build_task(created_at) WHERE status = 'pending';
CREATE INDEX idx_task_kbver   ON ai.kb_build_task(knowledge_base_version_id);
```
Worker 抢占语句：`SELECT ... FROM ai.kb_build_task WHERE status='pending' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1`。

---

## 6. 运行日志

### `ai.qa_retrieval_log`
检索日志（§10.2）。MVP 验收核心：能区分向量/关键词/最终分数与使用的 chunk。
```sql
CREATE TABLE ai.qa_retrieval_log (
    id                        bigserial PRIMARY KEY,
    session_id                bigint,              -- [XREF] public.qa_session(id)
    message_id                bigint NOT NULL,     -- [XREF] public.qa_message(id)
    raw_query                 text,
    normalized_query          text,
    keyword_query             text,
    semantic_query            text,
    retrieval_strategy        varchar(64),         -- strategy_code:version
    knowledge_base_version_id bigint,              -- [XREF] public.knowledge_base_version(id)
    chunk_id                  bigint,              -- [XREF] ai.knowledge_chunk(id)（弱引用，日志不级联删）
    rank_no                   int,
    vector_score              numeric(8,6),
    keyword_score             numeric(8,6),
    metadata_score            numeric(8,6),
    final_score               numeric(8,6),
    rerank_score              numeric(8,6),        -- MVP 空，阶段 4 写
    retrieval_channel         varchar(16)          -- vector / keyword / hybrid / rerank
        CHECK (retrieval_channel IN ('vector','keyword','hybrid','rerank')),
    matched_terms             jsonb,
    chunk_strategy_version    varchar(32),
    used_in_prompt            boolean DEFAULT false,
    prompt_position           int,
    reject_reason             varchar(64),         -- 拒答原因（命中行也可空）
    created_at                timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_retrlog_msg   ON ai.qa_retrieval_log(message_id);
CREATE INDEX idx_retrlog_sess  ON ai.qa_retrieval_log(session_id);
CREATE INDEX idx_retrlog_time  ON ai.qa_retrieval_log(created_at);
CREATE INDEX idx_retrlog_kbver ON ai.qa_retrieval_log(knowledge_base_version_id);
```
> `chunk_id` 不设 FK：日志要长期留存、可审计，即便 chunk 因版本归档被清理，日志仍应保留（§14 保留策略）。

### `ai.model_call_log`
模型调用日志（落地方案 §10.1、§14）。**不记密钥**。
```sql
CREATE TABLE ai.model_call_log (
    id            bigserial PRIMARY KEY,
    scenario      varchar(32),                     -- qa / embedding / question_gen / rerank / grade ...
    provider      varchar(64),
    model         varchar(128),
    message_id    bigint,                          -- 关联问答（可空）
    request_id    varchar(64),                     -- 网关 trace
    prompt_tokens int,
    completion_tokens int,
    total_tokens  int,
    latency_ms    int,
    success       boolean NOT NULL DEFAULT true,
    error_code    varchar(64),
    error_message text,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_modellog_time     ON ai.model_call_log(created_at);
CREATE INDEX idx_modellog_scenario ON ai.model_call_log(scenario, success);
```

---

## 7. RAG 评估（§10.2、§16）

### `ai.rag_eval_dataset`
```sql
CREATE TABLE ai.rag_eval_dataset (
    id          bigserial PRIMARY KEY,
    course_id   bigint NOT NULL,                   -- [XREF] public.course(id)
    name        varchar(128) NOT NULL,
    description  text,
    status      varchar(16) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','archived')),
    created_by  bigint,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
```

### `ai.rag_eval_case`
```sql
CREATE TABLE ai.rag_eval_case (
    id                          bigserial PRIMARY KEY,
    dataset_id                  bigint NOT NULL REFERENCES ai.rag_eval_dataset(id) ON DELETE CASCADE,
    question                    text NOT NULL,
    standard_answer             text,
    expected_knowledge_point_id bigint,            -- [XREF] public.knowledge_point(id)
    expected_sources            jsonb,             -- [{document_id,page_start,page_end}] 跨页多来源
    expected_keywords           jsonb,
    allow_reject                boolean NOT NULL DEFAULT false,
    difficulty                  varchar(16),
    question_type               varchar(16),
    status                      varchar(16) NOT NULL DEFAULT 'active',
    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_evalcase_ds ON ai.rag_eval_case(dataset_id);
```

### `ai.rag_eval_run`
```sql
CREATE TABLE ai.rag_eval_run (
    id                          bigserial PRIMARY KEY,
    dataset_id                  bigint NOT NULL REFERENCES ai.rag_eval_dataset(id) ON DELETE CASCADE,
    knowledge_base_version_id   bigint NOT NULL,   -- [XREF] public.knowledge_base_version(id)
    chunk_strategy_version      varchar(32),
    retrieval_strategy_version  varchar(32),
    prompt_version              varchar(32),
    status                      varchar(16) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running','success','failed')),
    started_at                  timestamptz,
    finished_at                 timestamptz,
    created_by                  bigint,
    created_at                  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_evalrun_ds ON ai.rag_eval_run(dataset_id);
```

### `ai.rag_eval_result`
```sql
CREATE TABLE ai.rag_eval_result (
    id               bigserial PRIMARY KEY,
    run_id           bigint NOT NULL REFERENCES ai.rag_eval_run(id) ON DELETE CASCADE,
    case_id          bigint NOT NULL REFERENCES ai.rag_eval_case(id) ON DELETE CASCADE,
    raw_query        text,
    normalized_query text,
    hit_knowledge_point boolean,
    hit_document     boolean,
    hit_page         boolean,
    recall_at_k      numeric(5,4),
    mrr              numeric(5,4),
    answer_correct   boolean,
    citation_correct boolean,
    reject_correct   boolean,
    failure_reason   varchar(32),                  -- chunk/改写/关键词/向量/排序/资料缺失/生成
    created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_evalresult_run ON ai.rag_eval_result(run_id);
```

---

## 8. 表清单与所属迁移建议

| 迁移 | 表 | 依赖 |
| --- | --- | --- |
| 0001_init | schema + extensions + `chunk_strategy`,`retrieval_strategy_config`,`prompt_template` | 无（纯 AI 配置表） |
| 0002_kb_pipeline | `document_page`,`embedding_index_version`,`keyword_index_version`,`knowledge_chunk`,`chunk_embedding`,`kb_build_task` | `chunk_embedding` 须在 `embedding_index_version` 之后建（intra-ai FK）；对 public 表仅逻辑引用、无 FK，**不依赖 RuoYi 表先建** |
| 0003_logs | `qa_retrieval_log`,`model_call_log` | 无硬依赖（对 public.qa_* 仅逻辑引用） |
| 0004_eval | `rag_eval_dataset/case/run/result` | 仅 intra-ai FK；对 public.course/knowledge_point 无 FK |

---

## 9. 本次细化中相对落地方案的增补/决策

1. **新增 `chunk_embedding` 表**：向量从 `knowledge_chunk` 拆出，按 (chunk, embedding_index_version) 存，支撑多模型评估对比与 HNSW 固定维度索引。
2. **`knowledge_chunk` 增 `tsv tsvector` 列 + GIN 索引**：落地方案的「PG 全文检索」落到具体列；jieba 预分词在应用层完成后写入。
3. **跨 schema 松耦合（已确认）**：指向 `public` 的列全为带索引普通列、无 FK；引用完整性与级联清理由应用层负责。
4. **日志表弱引用**：`qa_retrieval_log.chunk_id`、`model_call_log` 不设 FK，保证审计日志在数据归档后仍可留存（§14）。
5. **类型选择**：`bigserial` 主键对齐 RuoYi；`timestamptz`/`jsonb`/`numeric` 用于正确性与可查询性。
6. **`kb_build_task` 部分索引**（`WHERE status='pending'`）：配合 `FOR UPDATE SKIP LOCKED`，Worker 抢占高效。

---

## 10. 已确认的细颗粒决策

| # | 项 | 结论 |
| --- | --- | --- |
| 1 | 主键类型 | `bigserial`（对齐 RuoYi） |
| 2 | 跨 schema 外键 | **降级为松耦合普通列**（无 FK 指向 public，迁移互不依赖；级联清理走应用层）。`ai` 内部 FK 保留 |
| 3 | `document`/`document_version` 归属 | 归 Java（`public`）；FastAPI 仅改 `status` + 写 `ai.document_page` |
| 4 | 向量相似度 | 余弦 `vector_cosine_ops`（bge-m3 归一化后） |

下一步：把本套 DDL 转成 Alembic 迁移脚本（0001–0004）。
