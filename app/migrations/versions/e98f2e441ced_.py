"""empty message

Revision ID: e98f2e441ced
Revises: ae5c8c59a6fc
Create Date: 2016-10-03 17:52:34.576073

"""

# revision identifiers, used by Alembic.
revision = 'e98f2e441ced'
down_revision = 'ae5c8c59a6fc'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('actions', sa.Column('archived', sa.Boolean(), nullable=True))
    op.execute("""
        UPDATE actions
        SET archived = 'f'
    """)
    op.alter_column('actions', 'archived', nullable=False)

    op.add_column('actions', sa.Column('deleted', sa.Boolean(), nullable=True))
    op.execute("""
        UPDATE actions
        SET deleted = 'f'
    """)
    op.alter_column('actions', 'deleted', nullable=False)
    op.alter_column('actions', 'action_status_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('actions', 'ipp_latitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('actions', 'ipp_longitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('actions', 'rp_latitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('actions', 'rp_longitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('actions', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade():
    op.alter_column('actions', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('actions', 'rp_longitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('actions', 'rp_latitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('actions', 'ipp_longitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('actions', 'ipp_latitude',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('actions', 'action_status_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('actions', 'deleted')
    op.drop_column('actions', 'archived')
