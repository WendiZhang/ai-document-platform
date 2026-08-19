"""add chunk embeddings

Revision ID: fe85f30d6083
Revises: 74b5e95fcda3
Create Date: 2026-08-02 14:51:06.756510
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "fe85f30d6083"
down_revision: Union[str, Sequence[str], None] = "74b5e95fcda3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding",
            Vector(1536),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("document_chunks", "embedding")