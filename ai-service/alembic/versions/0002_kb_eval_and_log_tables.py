"""0002: knowledge base pipeline, evaluation, and logging tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# pgvector 索引参数（与 app.core.config 的 embedding_dim 一致）
EMBEDDING_DIM = 1024


def upgrade() -> None:
    # ── 知识库流水线 ──────────────────────────────────────────

    op.execute(
        """
        CREATE TABLE ai.document_page (
            id                  bigserial PRIMARY KEY,
            document_id         bigint NOT NULL,
            document_version_id bigint NOT NULL,
            page_number         int NOT NULL,
            title               varchar(512),
            text                text,
            tables_json         jsonb DEFAULT '[]'::jsonb,
            images_json         jsonb DEFAULT '[]'::jsonb,
            metadata_json       jsonb DEFAULT '{}'::jsonb,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_doc_page_version ON ai.document_page(document_version_id, page_number)"
    )

    op.execute(
        """
        CREATE TABLE ai.embedding_index_version (
            id                          bigserial PRIMARY KEY,
            knowledge_base_version_id   bigint NOT NULL,
            embedding_model             varchar(128) NOT NULL,
            embedding_model_version     varchar(64) NOT NULL,
            embedding_dim               int NOT NULL,
            vector_store                varchar(32) NOT NULL,
            collection_name             varchar(128),
            chunk_count                 int NOT NULL DEFAULT 0,
            status                      varchar(16) NOT NULL DEFAULT 'building',
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_emb_idx_version ON ai.embedding_index_version(knowledge_base_version_id)"
    )

    op.execute(
        """
        CREATE TABLE ai.keyword_index_version (
            id                          bigserial PRIMARY KEY,
            knowledge_base_version_id   bigint NOT NULL,
            index_engine                varchar(32) NOT NULL DEFAULT 'pg_fts',
            analyzer                    varchar(64),
            index_name                  varchar(128),
            chunk_count                 int NOT NULL DEFAULT 0,
            status                      varchar(16) NOT NULL DEFAULT 'building',
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_kw_idx_version ON ai.keyword_index_version(knowledge_base_version_id)"
    )

    op.execute(
        """
        CREATE TABLE ai.knowledge_chunk (
            id                          bigserial PRIMARY KEY,
            knowledge_base_version_id   bigint NOT NULL,
            course_id                   bigint NOT NULL,
            chapter_id                  bigint,
            knowledge_point_id          bigint,
            document_id                 bigint NOT NULL,
            document_version_id         bigint NOT NULL,
            chunk_text                  text NOT NULL,
            source_file                 varchar(512),
            page_start                  int,
            page_end                    int,
            chunk_hash                  varchar(64) NOT NULL,
            chunk_type                  varchar(32),
            chunk_strategy_version      varchar(32) NOT NULL,
            metadata_json               jsonb DEFAULT '{}'::jsonb,
            tsv                         tsvector,
            status                      varchar(16) NOT NULL DEFAULT 'active',
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_kc_version ON ai.knowledge_chunk(knowledge_base_version_id, status)"
    )
    op.execute("CREATE INDEX idx_kc_course ON ai.knowledge_chunk(course_id)")
    op.execute("CREATE INDEX idx_kc_document ON ai.knowledge_chunk(document_id)")
    op.execute("CREATE INDEX idx_kc_hash ON ai.knowledge_chunk(chunk_hash)")
    op.execute(
        "CREATE INDEX idx_kc_tsv ON ai.knowledge_chunk USING gin(tsv)"
    )

    op.execute(
        f"""
        CREATE TABLE ai.chunk_embedding (
            id                          bigserial PRIMARY KEY,
            chunk_id                    bigint NOT NULL
                REFERENCES ai.knowledge_chunk(id) ON DELETE CASCADE,
            embedding_index_version_id  bigint NOT NULL
                REFERENCES ai.embedding_index_version(id) ON DELETE CASCADE,
            embedding                   vector({EMBEDDING_DIM}) NOT NULL,
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_ce_chunk ON ai.chunk_embedding(chunk_id)"
    )
    op.execute(
        "CREATE INDEX idx_ce_index_version ON ai.chunk_embedding(embedding_index_version_id)"
    )
    # pgvector IVFFlat 索引（lists = sqrt(rows)，约为 100 对于 ~10k 行）
    op.execute(
        "CREATE INDEX idx_ce_embedding ON ai.chunk_embedding "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.execute(
        """
        CREATE TABLE ai.kb_build_task (
            id                          bigserial PRIMARY KEY,
            knowledge_base_version_id   bigint NOT NULL,
            task_type                   varchar(40) NOT NULL,
            status                      varchar(16) NOT NULL DEFAULT 'pending',
            current_step                varchar(64),
            progress                    int NOT NULL DEFAULT 0,
            payload_json                jsonb DEFAULT '{}'::jsonb,
            error_code                  varchar(64),
            error_message               text,
            retry_count                 int NOT NULL DEFAULT 0,
            started_at                  timestamptz,
            finished_at                 timestamptz,
            created_by                  bigint,
            updated_at                  timestamptz,
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_task_status ON ai.kb_build_task(status, created_at)"
    )
    op.execute(
        "CREATE INDEX idx_task_kb_version ON ai.kb_build_task(knowledge_base_version_id)"
    )

    # ── 运行日志 ─────────────────────────────────────────────

    op.execute(
        """
        CREATE TABLE ai.qa_retrieval_log (
            id                          bigserial PRIMARY KEY,
            session_id                  bigint,
            message_id                  bigint NOT NULL,
            raw_query                   text,
            normalized_query            text,
            keyword_query               text,
            semantic_query              text,
            retrieval_strategy          varchar(64),
            knowledge_base_version_id   bigint,
            chunk_id                    bigint,
            rank_no                     int,
            vector_score                numeric(8,6),
            keyword_score               numeric(8,6),
            metadata_score              numeric(8,6),
            final_score                 numeric(8,6),
            rerank_score                numeric(8,6),
            retrieval_channel           varchar(16),
            matched_terms               jsonb,
            chunk_strategy_version      varchar(32),
            used_in_prompt              boolean DEFAULT false,
            prompt_position             int,
            reject_reason               varchar(64),
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_ret_log_message ON ai.qa_retrieval_log(message_id)"
    )

    op.execute(
        """
        CREATE TABLE ai.model_call_log (
            id                  bigserial PRIMARY KEY,
            scenario            varchar(32),
            provider            varchar(64),
            model               varchar(128),
            message_id          bigint,
            request_id          varchar(64),
            prompt_tokens       int,
            completion_tokens   int,
            total_tokens        int,
            latency_ms          int,
            success             boolean NOT NULL DEFAULT true,
            error_code          varchar(64),
            error_message       text,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_model_log_message ON ai.model_call_log(message_id)"
    )

    # ── RAG 离线评估 ────────────────────────────────────────

    op.execute(
        """
        CREATE TABLE ai.rag_eval_dataset (
            id          bigserial PRIMARY KEY,
            course_id   bigint NOT NULL,
            name        varchar(128) NOT NULL,
            description text,
            status      varchar(16) NOT NULL DEFAULT 'active',
            created_by  bigint,
            updated_at  timestamptz,
            created_at  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_ev_dataset_course ON ai.rag_eval_dataset(course_id)")

    op.execute(
        """
        CREATE TABLE ai.rag_eval_case (
            id                          bigserial PRIMARY KEY,
            dataset_id                  bigint NOT NULL
                REFERENCES ai.rag_eval_dataset(id) ON DELETE CASCADE,
            question                    text NOT NULL,
            standard_answer             text,
            expected_knowledge_point_id bigint,
            expected_sources            jsonb,
            expected_keywords           jsonb,
            allow_reject                boolean NOT NULL DEFAULT false,
            difficulty                  varchar(16),
            question_type               varchar(16),
            status                      varchar(16) NOT NULL DEFAULT 'active',
            updated_at                  timestamptz,
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_ev_case_dataset ON ai.rag_eval_case(dataset_id)"
    )

    op.execute(
        """
        CREATE TABLE ai.rag_eval_run (
            id                          bigserial PRIMARY KEY,
            dataset_id                  bigint NOT NULL
                REFERENCES ai.rag_eval_dataset(id) ON DELETE CASCADE,
            knowledge_base_version_id   bigint NOT NULL,
            chunk_strategy_version      varchar(32),
            retrieval_strategy_version  varchar(32),
            prompt_version              varchar(32),
            status                      varchar(16) NOT NULL DEFAULT 'running',
            started_at                  timestamptz,
            finished_at                 timestamptz,
            created_by                  bigint,
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_ev_run_dataset ON ai.rag_eval_run(dataset_id)"
    )

    op.execute(
        """
        CREATE TABLE ai.rag_eval_result (
            id                  bigserial PRIMARY KEY,
            run_id              bigint NOT NULL
                REFERENCES ai.rag_eval_run(id) ON DELETE CASCADE,
            case_id             bigint NOT NULL
                REFERENCES ai.rag_eval_case(id) ON DELETE CASCADE,
            raw_query           text,
            normalized_query    text,
            hit_knowledge_point boolean,
            hit_document        boolean,
            hit_page            boolean,
            recall_at_k         numeric(5,4),
            mrr                 numeric(5,4),
            answer_correct      boolean,
            citation_correct    boolean,
            reject_correct      boolean,
            failure_reason      varchar(32),
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_ev_result_run ON ai.rag_eval_result(run_id)")
    op.execute("CREATE INDEX idx_ev_result_case ON ai.rag_eval_result(case_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai.rag_eval_result")
    op.execute("DROP TABLE IF EXISTS ai.rag_eval_run")
    op.execute("DROP TABLE IF EXISTS ai.rag_eval_case")
    op.execute("DROP TABLE IF EXISTS ai.rag_eval_dataset")
    op.execute("DROP TABLE IF EXISTS ai.model_call_log")
    op.execute("DROP TABLE IF EXISTS ai.qa_retrieval_log")
    op.execute("DROP TABLE IF EXISTS ai.kb_build_task")
    op.execute("DROP TABLE IF EXISTS ai.chunk_embedding")
    op.execute("DROP TABLE IF EXISTS ai.knowledge_chunk")
    op.execute("DROP TABLE IF EXISTS ai.keyword_index_version")
    op.execute("DROP TABLE IF EXISTS ai.embedding_index_version")
    op.execute("DROP TABLE IF EXISTS ai.document_page")
