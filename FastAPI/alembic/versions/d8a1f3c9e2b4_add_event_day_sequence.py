"""Add per-day event sequence fields

Revision ID: d8a1f3c9e2b4
Revises: c5d7e9f2a4b6
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa


revision = "d8a1f3c9e2b4"
down_revision = "c5d7e9f2a4b6"
branch_labels = None
depends_on = None


DAY_SEQUENCE_COLORS = ["orange", "green", "purple", "sky", "red"]


def _event_time_sort_key(row) -> tuple[int, int]:
    raw_time = (row.event_time or "").strip()
    if raw_time:
        parts = raw_time.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour * 60 + minute, row.id)
        except (TypeError, ValueError):
            pass
    date_value = row.date
    if hasattr(date_value, "hour"):
        minutes = date_value.hour * 60 + date_value.minute
        if minutes:
            return (minutes, row.id)
    date_text = str(date_value)
    if " " in date_text:
        time_text = date_text.split(" ", 1)[1].split(".", 1)[0]
        parts = time_text.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                minutes = hour * 60 + minute
                if minutes:
                    return (minutes, row.id)
        except (TypeError, ValueError):
            pass
    return (24 * 60, row.id)


def upgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("day_sequence_number", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("day_sequence_color", sa.String(length=30), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id, date, event_time
            FROM events
            WHERE is_deleted = 0
            ORDER BY date ASC, id ASC
            """
        )
    ).fetchall()

    grouped = {}
    for row in rows:
        event_date = str(row.date)[:10]
        grouped.setdefault(event_date, []).append(row)

    for day_events in grouped.values():
        for index, row in enumerate(sorted(day_events, key=_event_time_sort_key), start=1):
            color = DAY_SEQUENCE_COLORS[index - 1] if index <= len(DAY_SEQUENCE_COLORS) else None
            connection.execute(
                sa.text(
                    """
                    UPDATE events
                    SET day_sequence_number = :sequence_number,
                        day_sequence_color = :sequence_color
                    WHERE id = :event_id
                    """
                ),
                {
                    "sequence_number": index,
                    "sequence_color": color,
                    "event_id": row.id,
                },
            )


def downgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("day_sequence_color")
        batch_op.drop_column("day_sequence_number")
