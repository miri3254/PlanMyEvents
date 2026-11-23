"""Explicit menu-linked tablecloth rules; regular is the default."""
from alembic import op
import sqlalchemy as sa

revision = 'l5a6b7c8d9e0'
down_revision = 'k4f5a6b7c8d9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('menu_templates', sa.Column('tablecloth_profile', sa.String(30), nullable=False, server_default='regular'))
    table = sa.table('menu_templates', sa.column('menu_type'), sa.column('name'), sa.column('tablecloth_profile'))
    # Frozen mapping for existing templates; subsequent renaming cannot change it.
    for profile, keys in [
        ('shabbat', ['SHABBAT', 'שבת', 'תפריט שבת']),
        ('sweet', ['שולחן מתוק', 'אירוע מתוק']),
        ('shabbat_split', ['שבת מפוצל', 'שבת מפוצלת']),
    ]:
        op.execute(table.update().where(sa.or_(table.c.menu_type.in_(keys), table.c.name.in_(keys))).values(tablecloth_profile=profile))


def downgrade():
    op.drop_column('menu_templates', 'tablecloth_profile')
