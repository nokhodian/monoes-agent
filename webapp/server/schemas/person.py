from pydantic import BaseModel
from typing import List, Optional, Literal

class ContactDetail(BaseModel):
    type: str
    value: str

class PersonDTO(BaseModel):
    id: str
    platform_username: str
    full_name: str
    image_url: Optional[str] = None
    contact_details: List[ContactDetail] = []
    website: Optional[str] = None
    content_count: int = 0
    follower_count: Optional[str] = None
    following_count: int = 0
    introduction: Optional[str] = None
    is_verified: bool = False
    category: Optional[str] = None
    job_title: Optional[str] = None

class BatchCreatePeopleDTO(BaseModel):
    people: List[PersonDTO]
