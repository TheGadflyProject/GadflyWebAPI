"""empty message

Revision ID: 09ad3b11398d
Revises: 970e1697977b
Create Date: 2016-04-20 22:46:27.189268

"""

# revision identifiers, used by Alembic.
revision = '09ad3b11398d'
down_revision = '970e1697977b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('answer_choice',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('question_id', sa.String(), nullable=True),
    sa.Column('answer_choice', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('answer_choice')
    ### end Alembic commands ###
