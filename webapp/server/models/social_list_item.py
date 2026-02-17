from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.sqlite import JSON
from ..db import Base

class SocialListItem(Base):
    __tablename__ = "social_list_items"
    id = Column(String, primary_key=True, index=True)
    listId = Column(String, index=True)
    platform = Column(String, index=True)
    platform_username = Column(String, index=True)
    image_url = Column(String)
    url = Column(String)
    full_name = Column(String)
    contact_details = Column(JSON)
    follower_count = Column(Integer, default=0)
