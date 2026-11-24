"""Dish yield (quantity + container), dish notes, nullable guests/ingredient amounts (2026-11-24).

Caterer counts recipes in containers (גסטרונום / מגש ...) as well as guests.
Ingredients whose amount/unit is missing in the source recipe are kept with NULLs.
"""
from alembic import op
import sqlalchemy as sa

revision = 'r1a2b3c4d5e6'
down_revision = 'q0f1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('dishes') as batch:
        batch.add_column(sa.Column('yield_quantity', sa.Float(), nullable=True))
        batch.add_column(sa.Column('yield_unit', sa.String(100), nullable=True))
        batch.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch.alter_column('serving_size', existing_type=sa.Float(), nullable=True)
    with op.batch_alter_table('dish_ingredients') as batch:
        batch.add_column(sa.Column('note', sa.Text(), nullable=True))
        batch.alter_column('quantity', existing_type=sa.Float(), nullable=True)
        batch.alter_column('unit', existing_type=sa.String(10), nullable=True)


def downgrade():
    with op.batch_alter_table('dish_ingredients') as batch:
        batch.drop_column('note')
    with op.batch_alter_table('dishes') as batch:
        batch.drop_column('notes')
        batch.drop_column('yield_unit')
        batch.drop_column('yield_quantity')
