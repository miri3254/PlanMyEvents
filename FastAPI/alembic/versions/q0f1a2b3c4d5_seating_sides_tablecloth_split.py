"""Hall seating per side and per-event tablecloth shape split (caterer document instructions 2026-11)."""
from alembic import op
import sqlalchemy as sa
revision = 'q0f1a2b3c4d5'
down_revision = 'p9e0f1a2b3c4'
branch_labels = None
depends_on = None


def upgrade():
    # [{"side": "גברים", "places": 120, "arrangement": "ארוכים"}, ...]
    op.add_column('events', sa.Column('seating_sides', sa.JSON(), nullable=True))
    # {"rectangle": 8, "square": 4}; total comes from the workbook rule (portions / 8 + spare)
    op.add_column('event_calculation_settings', sa.Column('tablecloth_split', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('event_calculation_settings', 'tablecloth_split')
    op.drop_column('events', 'seating_sides')
