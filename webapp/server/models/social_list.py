from sqlalchemy import Column, String, Integer
from ..db import Base

class SocialList(Base):
    __tablename__ = "social_lists"
    id = Column(String, primary_key=True, index=True)
    listType = Column(String, index=True)
    name = Column(String, index=True)
    itemCount = Column(Integer, default=0)
    email = Column(String)
