"""Per-event desserts toggle and free "other drink" rows (caterer list, user decisions 2026-11-24)."""
from alembic import op
import sqlalchemy as sa
revision = 's2b3c4d5e6f7'
down_revision = 'q0f1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade():
    # Desserts: 1.5 per guest split ~equally between 4 types, in every menu (can be turned off per event)
    op.add_column('event_calculation_settings',
                  sa.Column('desserts_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
    # [{"name": "מים בטעמים", "quantity": 12, "notes": "..."}] – manual quantity, no formula
    op.add_column('event_calculation_settings', sa.Column('other_drinks', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('event_calculation_settings', 'other_drinks')
    op.drop_column('event_calculation_settings', 'desserts_enabled')
