"""Structured serving alternatives; existing definitions remain intact."""
from alembic import op
import sqlalchemy as sa

revision = 'm6b7c8d9e0f1'
down_revision = 'l5a6b7c8d9e0'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('dish_serving_sets', sa.Column('serving_mode', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('dish_serving_sets', 'serving_mode')
