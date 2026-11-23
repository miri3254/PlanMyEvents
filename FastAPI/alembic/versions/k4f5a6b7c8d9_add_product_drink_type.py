"""One active inventory product per drink type; no stock merges or data changes."""
from alembic import op
import sqlalchemy as sa

revision = "k4f5a6b7c8d9"
down_revision = "j3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("products", sa.Column("drink_type", sa.String(30), nullable=True))
    op.create_index("uq_products_active_drink_type", "products", ["drink_type"],
                    unique=True,
                    sqlite_where=sa.text("is_deleted = 0 AND drink_type IS NOT NULL"),
                    postgresql_where=sa.text("is_deleted = false AND drink_type IS NOT NULL"))


def downgrade():
    op.drop_index("uq_products_active_drink_type", table_name="products")
    op.drop_column("products", "drink_type")
