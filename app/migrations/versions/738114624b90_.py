"""empty message

Revision ID: 738114624b90
Revises: 3a8554125a27
Create Date: 2016-09-10 16:49:09.075965

"""

# revision identifiers, used by Alembic.
revision = '738114624b90'
down_revision = '3a8554125a27'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'users', ['login'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    ### end Alembic commands ###
