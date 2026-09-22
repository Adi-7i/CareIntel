# embedding_dimension_azure

"""embedding_dimension_azure

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-22 18:05:46.037968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Delete all existing demo embeddings as they are not 1536-dim and not semantically meaningful
    op.execute("DELETE FROM chunk_embeddings;")

    # 2. Alter the vector column dimension from 768 to 1536
    op.execute("ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(1536);")

    # 3. Recreate the HNSW index
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_hnsw;")
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_hnsw "
        "ON chunk_embeddings USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    # 1. Delete the 1536-dim vectors
    op.execute("DELETE FROM chunk_embeddings;")

    # 2. Alter back to 768
    op.execute("ALTER TABLE chunk_embeddings ALTER COLUMN embedding TYPE vector(768);")

    # 3. Recreate index
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_hnsw;")
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_hnsw "
        "ON chunk_embeddings USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )
