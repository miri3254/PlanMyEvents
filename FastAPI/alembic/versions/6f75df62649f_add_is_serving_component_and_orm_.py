"""add_is_serving_component_and_orm_relationships

Revision ID: 6f75df62649f
Revises: 
Create Date: 2026-02-10 13:05:04.321249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f75df62649f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('dish_ingredients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_serving_component', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    with op.batch_alter_table('dish_ingredients', schema=None) as batch_op:
        batch_op.drop_column('is_serving_component')
