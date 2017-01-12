"""empty message

Revision ID: 550e330895c2
Revises: e98f2e441ced
Create Date: 2016-10-04 14:07:45.910987

"""

# revision identifiers, used by Alembic.
revision = '550e330895c2'
down_revision = 'e98f2e441ced'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('analyses', sa.Column('deleted', sa.Boolean(), nullable=True))
    op.execute("UPDATE analyses SET deleted = 'f' ")
    op.alter_column('analyses', 'deleted', nullable=False)


def downgrade():
    op.drop_column('analyses', 'deleted')
