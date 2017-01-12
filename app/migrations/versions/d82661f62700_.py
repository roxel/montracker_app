"""empty message

Revision ID: d82661f62700
Revises: 738114624b90
Create Date: 2016-09-29 18:54:27.973823

"""

# revision identifiers, used by Alembic.
revision = 'd82661f62700'
down_revision = '738114624b90'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'model_types', ['name'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'model_types', type_='unique')
    ### end Alembic commands ###
