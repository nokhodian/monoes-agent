from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.sqlite import JSON
from ..db import Base

class ActionTarget(Base):
    __tablename__ = "action_targets"
    id = Column(String, primary_key=True, index=True)
    actionId = Column(String, index=True)
    personId = Column(String, index=True)
    platform = Column(String, index=True)
    link = Column(String)
    sourceType = Column(String)
    status = Column(String, index=True)
    lastInteractedAt = Column(String)
    commentText = Column(String)
    meta = Column("metadata", JSON)
