"""empty message

Revision ID: 9a54d0609a88
Revises: d82661f62700
Create Date: 2016-10-03 11:05:50.806908

"""

# revision identifiers, used by Alembic.
from app.processor.models import ModelType
from sqlalchemy.orm import Session

revision = '9a54d0609a88'
down_revision = 'd82661f62700'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('model_types', sa.Column('complex', sa.Boolean(), nullable=True))
    op.execute("""
        UPDATE model_types
        SET complex = 'f'
    """)
    op.alter_column('model_types', 'complex', nullable=False)

    bind = op.get_bind()
    session = Session(bind=bind)

    for model_type in session.query(ModelType):
        if model_type.name in ["union", "segments"]:
            model_type.complex = True

    session.commit()


def downgrade():
    op.drop_column('model_types', 'complex')
