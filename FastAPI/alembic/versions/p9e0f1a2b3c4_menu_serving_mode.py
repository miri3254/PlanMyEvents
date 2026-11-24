"""Menu serving defaults and explicit event dish overrides."""
from alembic import op
import sqlalchemy as sa
revision = 'p9e0f1a2b3c4'
down_revision = 'o8d9e0f1a2b3'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('dish_menu_mappings', sa.Column('default_serving_mode', sa.String(20), nullable=True))
    op.add_column('event_dishes', sa.Column('serving_mode', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('event_dishes', 'serving_mode')
    op.drop_column('dish_menu_mappings', 'default_serving_mode')
