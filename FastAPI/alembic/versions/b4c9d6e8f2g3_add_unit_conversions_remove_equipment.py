"""Add unit_conversions table and remove dish_equipment

This migration:
1. Creates the unit_conversions table for storing unit conversion factors
2. Drops the dish_equipment table (equipment tracking removed from dishes)

Revision ID: b4c9d6e8f2g3
Revises: a3b8c5d7e9f1
Create Date: 2026-03-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4c9d6e8f2g3'
down_revision = 'a3b8c5d7e9f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create unit_conversions table
    op.create_table(
        'unit_conversions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('from_unit', sa.Enum(
            'ק"ג', 'גרם', 'מ"ג', 'ליטר', 'מ"ל', 'יחידות', 
            'אריזה', 'מגש', 'כף', 'כפית', 'קורט', 'חבילה',
            name='unittype'
        ), nullable=False),
        sa.Column('to_unit', sa.Enum(
            'ק"ג', 'גרם', 'מ"ג', 'ליטר', 'מ"ל', 'יחידות', 
            'אריזה', 'מגש', 'כף', 'כפית', 'קורט', 'חבילה',
            name='unittype'
        ), nullable=False),
        sa.Column('factor', sa.Float(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('from_unit', 'to_unit', name='uix_from_to_unit')
    )
    
    # Drop dish_equipment table
    op.drop_table('dish_equipment')


def downgrade() -> None:
    # Recreate dish_equipment table
    op.create_table(
        'dish_equipment',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dish_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Drop unit_conversions table
    op.drop_table('unit_conversions')
