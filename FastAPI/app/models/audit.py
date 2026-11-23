"""
Audit log model — lightweight action log for main entities.
"""

from sqlalchemy import Column, String, Integer, JSON

from app.db.base import BaseModel


class AuditLog(BaseModel):
    """
    Records create / update / delete / status-change actions
    on the four main entities: event, dish, product, tool.
    """

    __tablename__ = "audit_logs"

    entity_type = Column(String(50), nullable=False, index=True)   # "event", "dish", …
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)                     # AuditAction value
    details = Column(JSON, nullable=True)                           # optional extra info
