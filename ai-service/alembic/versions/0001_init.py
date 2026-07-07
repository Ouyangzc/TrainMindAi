"""0001 init: schema + extensions + 配置类表

Revision ID: 0001
Revises:
Create Date: 2026-06-17

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        """
        CREATE TABLE ai.chunk_strategy (
            id               bigserial PRIMARY KEY,
            strategy_code    varchar(64) NOT NULL,
            strategy_version varchar(32) NOT NULL,
            chunk_method     varchar(32) NOT NULL
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
        )
        """
    )

    op.execute(
        """
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
            min_score_threshold numeric(5,4) NOT NULL DEFAULT 0.0,
            rerank_enabled      boolean NOT NULL DEFAULT false,
            enabled             boolean NOT NULL DEFAULT true,
            created_by          bigint,
            created_at          timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_retr_strategy UNIQUE (strategy_code, strategy_version)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE ai.prompt_template (
            id             bigserial PRIMARY KEY,
            prompt_code    varchar(64) NOT NULL,
            prompt_version varchar(32) NOT NULL,
            scenario       varchar(32) NOT NULL
                CHECK (
                    scenario IN (
                        'qa','question_gen','diagnose',
                        'reteach','grade','quality_check'
                    )
                ),
            prompt_content text NOT NULL,
            output_schema  jsonb,
            enabled        boolean NOT NULL DEFAULT true,
            created_by     bigint,
            created_at     timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_prompt UNIQUE (prompt_code, prompt_version)
        )
        """
    )
    op.execute("CREATE INDEX idx_prompt_scenario ON ai.prompt_template(scenario, enabled)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai.prompt_template")
    op.execute("DROP TABLE IF EXISTS ai.retrieval_strategy_config")
    op.execute("DROP TABLE IF EXISTS ai.chunk_strategy")
    # 扩展与 schema 不在 downgrade 中删除（可能被其他对象依赖）
