from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.sqlite import JSON
from ..db import Base

class Thread(Base):
    __tablename__ = "threads"
    id = Column(String, primary_key=True, index=True)
    socialUserId = Column(String, index=True)
    meta = Column("metadata", JSON)
    messages = Column(JSON)
