"""Create table "Dataset"

Revision ID: 3cd7dd11f91f
Revises:
Create Date: 2017-10-23 17:38:22.980295

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy.sql.functions as sa_functions


# revision identifiers, used by Alembic.
revision = '3cd7dd11f91f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'Dataset',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('dcat', postgresql.JSONB(), nullable=False),
        sa.Index('idx_dcat_jsonb_path_ops',
                 sa.text("dcat jsonb_path_ops"),
                 postgresql_using='gin')
    )


def downgrade():
    op.drop_table('Dataset')
