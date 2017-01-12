"""empty message

Revision ID: ae5c8c59a6fc
Revises: 9a54d0609a88
Create Date: 2016-10-03 16:23:04.913513

"""

# revision identifiers, used by Alembic.
revision = 'ae5c8c59a6fc'
down_revision = '9a54d0609a88'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_unique_constraint(None, 'action_statuses', ['name'])
    op.create_unique_constraint(None, 'model_statuses', ['name'])
    op.create_unique_constraint(None, 'person_types', ['name'])


def downgrade():
    op.drop_constraint(None, 'person_types', type_='unique')
    op.drop_constraint(None, 'model_statuses', type_='unique')
    op.drop_constraint(None, 'action_statuses', type_='unique')
