"""0004: add QA answer observation logs

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-30

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE ai.qa_retrieval_log ADD COLUMN IF NOT EXISTS language varchar(16)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai.qa_answer_observation (
            id                          bigserial PRIMARY KEY,
            course_id                   bigint,
            session_id                  bigint,
            message_id                  bigint NOT NULL,
            knowledge_base_version_id   bigint,
            retrieval_log_ref           bigint,
            model_call_log_ref          bigint,
            request_id                  varchar(64),
            language                    varchar(16),
            retrieval_channel           varchar(16),
            answer_status               varchar(32),
            reject_reason               varchar(64),
            warnings                    jsonb,
            source_count                int,
            cited_source_count          int,
            invalid_citation_count      int,
            weak_citation_count         int,
            no_valid_citation           boolean,
            top_score                   numeric(8,6),
            retrieval_latency_ms        int,
            llm_latency_ms              int,
            first_token_ms              int,
            total_latency_ms            int,
            created_at                  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_qa_obs_message "
        "ON ai.qa_answer_observation(message_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_qa_obs_course_created "
        "ON ai.qa_answer_observation(course_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_qa_obs_status "
        "ON ai.qa_answer_observation(answer_status, retrieval_channel)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai.qa_answer_observation")
    op.execute("ALTER TABLE ai.qa_retrieval_log DROP COLUMN IF EXISTS language")
