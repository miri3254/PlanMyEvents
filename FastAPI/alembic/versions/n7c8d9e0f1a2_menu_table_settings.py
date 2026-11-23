"""Editable inventory mappings for automatic menu place settings."""
from alembic import op
import sqlalchemy as sa
revision = 'n7c8d9e0f1a2'
down_revision = 'm6b7c8d9e0f1'
branch_labels = None
depends_on = None
def upgrade():
    op.add_column('menu_templates', sa.Column('table_setting_items', sa.JSON(), nullable=True))
def downgrade():
    op.drop_column('menu_templates', 'table_setting_items')
