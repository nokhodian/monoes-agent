from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.sqlite import JSON
from ..db import Base

class Person(Base):
    __tablename__ = "people"
    id = Column(String, primary_key=True, index=True)
    platform_username = Column(String, index=True)
    full_name = Column(String)
    image_url = Column(String)
    contact_details = Column(JSON)
    website = Column(String)
    content_count = Column(Integer, default=0)
    follower_count = Column(String)
    following_count = Column(Integer, default=0)
    introduction = Column(String)
    is_verified = Column(Boolean, default=False)
    category = Column(String)
    job_title = Column(String)
