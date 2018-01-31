"""Create table "Dataset"

Revision ID: 3cd7dd11f91f
Revises:
Create Date: 2017-10-23 17:38:22.980295

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3cd7dd11f91f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'Dataset',
        sa.Column('id', sa.String, nullable=False, primary_key=True),
        sa.Column('doc', postgresql.JSONB(), nullable=False),
        sa.Column('etag', sa.String, nullable=False),
        sa.Column('searchable_text', postgresql.TSVECTOR, nullable=False),
        sa.Column('lang', sa.String, nullable=False, index=True),
        sa.Index('idx_id_etag', 'id', 'etag'),
        sa.Index('idx_full_text_search', 'searchable_text', postgresql_using='gin')
    )


def downgrade():
    op.drop_table('Dataset')
