"""empty message

Revision ID: 3a8554125a27
Revises: None
Create Date: 2016-09-10 13:02:41.307508

"""

# revision identifiers, used by Alembic.
revision = '3a8554125a27'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('action_statuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model_statuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('person_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=64), nullable=False),
    sa.Column('password', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('actions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('action_status_id', sa.Integer(), nullable=False),
    sa.Column('ipp_latitude', sa.Float(), nullable=False),
    sa.Column('ipp_longitude', sa.Float(), nullable=False),
    sa.Column('rp_latitude', sa.Float(), nullable=False),
    sa.Column('rp_longitude', sa.Float(), nullable=False),
    sa.Column('lost_time', sa.DateTime(), nullable=False),
    sa.Column('creation_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['action_status_id'], ['action_statuses.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('available_analyses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model_type_id', sa.Integer(), nullable=True),
    sa.Column('person_type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['model_type_id'], ['model_types.id'], ),
    sa.ForeignKeyConstraint(['person_type_id'], ['person_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('analyses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('ipp_latitude', sa.Float(), nullable=True),
    sa.Column('ipp_longitude', sa.Float(), nullable=True),
    sa.Column('rp_latitude', sa.Float(), nullable=True),
    sa.Column('rp_longitude', sa.Float(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('lost_time', sa.DateTime(), nullable=True),
    sa.Column('creation_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['action_id'], ['actions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('models',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('analysis_id', sa.Integer(), nullable=False),
    sa.Column('model_type_id', sa.Integer(), nullable=False),
    sa.Column('status_id', sa.Integer(), nullable=False),
    sa.Column('result_id', sa.CHAR(length=64), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
    sa.ForeignKeyConstraint(['model_type_id'], ['model_types.id'], ),
    sa.ForeignKeyConstraint(['status_id'], ['model_statuses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('analysis_id', sa.Integer(), nullable=False),
    sa.Column('person_type_id', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
    sa.ForeignKeyConstraint(['person_type_id'], ['person_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('layers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('layers_id', sa.String(length=256), nullable=False),
    sa.Column('model_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['model_id'], ['models.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('model_weights',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model_id', sa.Integer(), nullable=False),
    sa.Column('child_model_id', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['child_model_id'], ['models.id'], ),
    sa.ForeignKeyConstraint(['model_id'], ['models.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('model_weights')
    op.drop_table('layers')
    op.drop_table('profiles')
    op.drop_table('models')
    op.drop_table('analyses')
    op.drop_table('available_analyses')
    op.drop_table('actions')
    op.drop_table('users')
    op.drop_table('person_types')
    op.drop_table('model_types')
    op.drop_table('model_statuses')
    op.drop_table('action_statuses')
    ### end Alembic commands ###
