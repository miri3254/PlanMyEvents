"""Add pricing fields to menu_templates and events tables

Adds to menu_templates:
- real_dishes_extra_per_guest: Float - extra charge per guest for real dishes

Adds to events:
- is_real_dishes: Boolean - whether using real dishes (not disposable)
- real_dishes_extra_per_guest: Float - snapshot from template
- calculated_price: Float - automatically calculated total
- final_price: Float - editable final price
- discount_percent: Float - calculated discount percentage
- discount_amount: Float - calculated discount amount

Renames:
- is_disposable → removed (replaced by is_real_dishes with opposite meaning)

Revision ID: c5d7e9f2a4b6
Revises: b4c9d6e8f2g3
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5d7e9f2a4b6'
down_revision = 'b4c9d6e8f2g3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new column to menu_templates
    with op.batch_alter_table('menu_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('real_dishes_extra_per_guest', sa.Float(), nullable=True, server_default='0.0'))

    # Add new pricing columns to events
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_real_dishes', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('real_dishes_extra_per_guest', sa.Float(), nullable=True, server_default='0.0'))
        batch_op.add_column(sa.Column('calculated_price', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('final_price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('discount_percent', sa.Float(), nullable=True, server_default='0.0'))
        batch_op.add_column(sa.Column('discount_amount', sa.Float(), nullable=True, server_default='0.0'))
        # Remove old is_disposable column
        batch_op.drop_column('is_disposable')


def downgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_disposable', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.drop_column('discount_amount')
        batch_op.drop_column('discount_percent')
        batch_op.drop_column('final_price')
        batch_op.drop_column('calculated_price')
        batch_op.drop_column('real_dishes_extra_per_guest')
        batch_op.drop_column('is_real_dishes')

    with op.batch_alter_table('menu_templates', schema=None) as batch_op:
        batch_op.drop_column('real_dishes_extra_per_guest')
