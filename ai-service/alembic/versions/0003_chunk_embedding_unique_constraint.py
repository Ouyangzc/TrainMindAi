"""0003: add chunk embedding upsert constraint

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE ai.chunk_embedding "
        "ADD CONSTRAINT uq_chunk_embedding_chunk_index_version "
        "UNIQUE (chunk_id, embedding_index_version_id)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE ai.chunk_embedding "
        "DROP CONSTRAINT IF EXISTS uq_chunk_embedding_chunk_index_version"
    )
