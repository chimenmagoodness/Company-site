"""Upgrade migration

Revision ID: ad21b72899e6
Revises: 689986c0af14
Create Date: 2024-12-17 17:10:45.416578

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad21b72899e6'
down_revision = '689986c0af14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('admin_code')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_code',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('code_name', sa.VARCHAR(length=50), nullable=False),
    sa.Column('code_value', sa.VARCHAR(length=200), nullable=False),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code_name')
    )
    # ### end Alembic commands ###
