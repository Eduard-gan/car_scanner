"""'interest'

Revision ID: 5a676fc46bec
Revises: 537829a23cd4
Create Date: 2023-04-30 15:06:56.320366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a676fc46bec'
down_revision = '537829a23cd4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ad', sa.Column('interesting', sa.Boolean(), server_default='false', nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ad', 'interesting')
    # ### end Alembic commands ###
