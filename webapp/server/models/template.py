from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.sqlite import JSON
from ..db import Base

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    subject = Column(String)
    body = Column(String)
    meta = Column("metadata", JSON)
