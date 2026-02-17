from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
from ..db import Base

class Action(Base):
    __tablename__ = "actions"
    id = Column(String, primary_key=True, index=True)
    createdAt = Column(Integer, index=True)
    createdBy = Column(String)
    ownerId = Column(String, index=True)
    title = Column(String)
    type = Column(String, index=True)
    state = Column(String, index=True)
    disabled = Column(Boolean, default=False)
    targetPlatform = Column(String, index=True)
    position = Column(Integer, default=0)
    cost = Column(Integer, default=0)
    actionExecutionCount = Column(Integer, default=0)
    contentSubject = Column(String)
    contentMessage = Column(String)
    contentBlobURL = Column(JSON)
    scheduledDate = Column(String)
    executionInterval = Column(Integer, default=0)
    startDate = Column(String)
    endDate = Column(String)
    campaignID = Column(String)
    created_at_ts = Column(DateTime, default=datetime.utcnow)
