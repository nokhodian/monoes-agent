import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.social_list import SocialList
from ..models.social_list_item import SocialListItem

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/social-lists")
def list_social_lists(db: Session = Depends(get_db)):
    items = db.query(SocialList).all()
    data = []
    for s in items:
        data.append({
            "listType": s.listType,
            "name": s.name,
            "id": s.id,
            "itemCount": s.itemCount,
            "email": s.email
        })
    return {"message": "Successful", "data": data}

@router.get("/social-lists/{list_id}/items")
def list_social_items(list_id: str, db: Session = Depends(get_db)):
    items = db.query(SocialListItem).filter(SocialListItem.listId == list_id).all()
    data = []
    for i in items:
        data.append({
            "id": i.id,
            "contact_details": i.contact_details or [],
            "follower_count": i.follower_count,
            "platform": i.platform.lower(),
            "platform_username": i.platform_username,
            "updated_at": "",
            "full_name": i.full_name,
            "image_url": i.image_url or "",
            "url": i.url
        })
    return {"message": "Successful", "data": data}

@router.post("/social-lists/{list_id}/item")
def create_social_item(list_id: str, payload: dict, db: Session = Depends(get_db)):
    sid = str(uuid.uuid4())
    i = SocialListItem(
        id=sid,
        listId=list_id,
        platform=payload.get("platform", ""),
        platform_username=payload.get("platform_username", ""),
        image_url=payload.get("image_url", ""),
        url=payload.get("url", ""),
        full_name=payload.get("full_name", ""),
        contact_details=payload.get("contact_details") or [],
        follower_count=payload.get("follower_count") or 0
    )
    db.add(i)
    # increment count
    s = db.query(SocialList).get(list_id)
    if s:
        s.itemCount = (s.itemCount or 0) + 1
    db.commit()
    return {"message": "Successful", "id": sid}

@router.post("/social-lists/{list_id}/items")
def create_social_items(list_id: str, payload: dict, db: Session = Depends(get_db)):
    items = payload.get("items") or []
    created = []
    for payload_item in items:
        sid = str(uuid.uuid4())
        i = SocialListItem(
            id=sid,
            listId=list_id,
            platform=payload_item.get("platform", ""),
            platform_username=payload_item.get("platform_username", ""),
            image_url=payload_item.get("image_url", ""),
            url=payload_item.get("url", ""),
            full_name=payload_item.get("full_name", ""),
            contact_details=payload_item.get("contact_details") or [],
            follower_count=payload_item.get("follower_count") or 0
        )
        db.add(i)
        created.append(sid)
    s = db.query(SocialList).get(list_id)
    if s:
        s.itemCount = (s.itemCount or 0) + len(created)
    db.commit()
    return {"message": "Successful", "created": created}

@router.put("/social-users")
def update_social_users(payload: dict, db: Session = Depends(get_db)):
    items = payload.get("items") or []
    # For parity, upsert into SocialListItem by platform_username if a default list exists
    updated = 0
    for item in items:
        platform_username = item.get("platform_username")
        q = db.query(SocialListItem).filter(SocialListItem.platform_username == platform_username)
        i = q.first()
        if i:
            i.image_url = item.get("image_url", i.image_url)
            i.url = item.get("url", i.url)
            i.full_name = item.get("full_name", i.full_name)
            i.contact_details = item.get("contact_details") or i.contact_details
            i.follower_count = item.get("follower_count") or i.follower_count
            updated += 1
    db.commit()
    return {"message": "Successful", "updated": updated}
