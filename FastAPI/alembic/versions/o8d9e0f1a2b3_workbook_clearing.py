"""Configurable installment rates from the supplied workbook."""
from alembic import op
import sqlalchemy as sa
revision = 'o8d9e0f1a2b3'
down_revision = 'n7c8d9e0f1a2'
branch_labels = None
depends_on = None
def upgrade():
    op.add_column('event_calculation_settings', sa.Column('credit_card_installments', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('event_calculation_settings', sa.Column('credit_card_rate', sa.Float(), nullable=True))
    op.add_column('event_calculation_settings', sa.Column('credit_card_vat_multiplier', sa.Float(), nullable=False, server_default='1.18'))
def downgrade():
    for column in ('credit_card_vat_multiplier', 'credit_card_rate', 'credit_card_installments'):
        op.drop_column('event_calculation_settings', column)
