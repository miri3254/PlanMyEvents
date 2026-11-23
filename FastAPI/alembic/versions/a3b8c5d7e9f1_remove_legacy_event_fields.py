"""Remove legacy fields from events table

Removes: event_type, location, owner1_name, owner1_phone, owner1_email,
         owner2_name, owner2_phone, owner2_email, contact_name, contact_phone

These fields were replaced by:
- event_type → menu_type (MenuType enum)
- location → address + city
- owner1/2/contact → event_owners table

Revision ID: a3b8c5d7e9f1
Revises: 6f75df62649f
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3b8c5d7e9f1'
down_revision = '6f75df62649f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('event_type')
        batch_op.drop_column('location')
        batch_op.drop_column('owner1_name')
        batch_op.drop_column('owner1_phone')
        batch_op.drop_column('owner1_email')
        batch_op.drop_column('owner2_name')
        batch_op.drop_column('owner2_phone')
        batch_op.drop_column('owner2_email')
        batch_op.drop_column('contact_name')
        batch_op.drop_column('contact_phone')


def downgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contact_phone', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('contact_name', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner2_email', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner2_phone', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('owner2_name', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner1_email', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner1_phone', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('owner1_name', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('location', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('event_type', sa.VARCHAR(length=100), nullable=True))
