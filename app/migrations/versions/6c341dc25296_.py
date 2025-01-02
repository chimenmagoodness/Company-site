"""empty message

Revision ID: 6c341dc25296
Revises: 7d0324860550
Create Date: 2024-12-19 08:48:34.042903

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision = '6c341dc25296'
down_revision = '7d0324860550'
branch_labels = None
depends_on = None


# op.add_column('user', sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='0'))
bind = op.get_bind()
insp = reflection.Inspector.from_engine(bind)
if 'is_confirmed' not in [column['name'] for column in insp.get_columns('user')]:
    op.add_column('user', sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='0'))


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_user')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confirmed_on', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('confirmed_on')

    op.create_table('_alembic_tmp_user',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=150), nullable=False),
    sa.Column('email', sa.VARCHAR(length=150), nullable=False),
    sa.Column('password', sa.VARCHAR(length=200), nullable=False),
    sa.Column('is_admin', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.Column('role', sa.VARCHAR(length=50), nullable=True),
    sa.Column('position', sa.VARCHAR(length=70), nullable=True),
    sa.Column('is_verified', sa.BOOLEAN(), nullable=True),
    sa.Column('is_confirmed', sa.BOOLEAN(), server_default=sa.text('0'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    # ### end Alembic commands ###