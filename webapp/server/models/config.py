from sqlalchemy import Column, String
from sqlalchemy.dialects.sqlite import JSON
from ..db import Base

class ConfigEntry(Base):
    __tablename__ = "configs"
    name = Column(String, primary_key=True, index=True)
    data = Column(JSON)
