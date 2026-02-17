import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.person import Person
from ..schemas.person import PersonDTO, BatchCreatePeopleDTO

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/people/{id}")
def get_person(id: str, db: Session = Depends(get_db)):
    p = db.query(Person).get(id)
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    return {"data": {"person": {
        "id": p.id,
        "platform_username": p.platform_username,
        "full_name": p.full_name,
        "image_url": p.image_url,
        "contact_details": p.contact_details or [],
        "website": p.website,
        "content_count": p.content_count,
        "follower_count": p.follower_count,
        "following_count": p.following_count,
        "introduction": p.introduction,
        "is_verified": p.is_verified,
        "category": p.category,
        "job_title": p.job_title
    }}}

@router.get("/people")
def list_people(q: str | None = None, platform: str | None = None, username: str | None = None, page: int = 1, perPage: int = 20, db: Session = Depends(get_db)):
    query = db.query(Person)
    if username:
        query = query.filter(Person.platform_username.ilike(f"%{username}%"))
    if q:
        query = query.filter(Person.full_name.ilike(f"%{q}%"))
    total = query.count()
    items = query.offset((page - 1) * perPage).limit(perPage).all()
    data = []
    for p in items:
        data.append({
            "id": p.id,
            "platform_username": p.platform_username,
            "full_name": p.full_name,
            "image_url": p.image_url,
            "contact_details": p.contact_details or [],
            "website": p.website,
            "content_count": p.content_count,
            "follower_count": p.follower_count,
            "following_count": p.following_count,
            "introduction": p.introduction,
            "is_verified": p.is_verified,
            "category": p.category,
            "job_title": p.job_title
        })
    return {"data": {"people": data, "totalCount": total}}

@router.post("/people:batch")
def batch_create(payload: BatchCreatePeopleDTO, db: Session = Depends(get_db)):
    created = []
    for item in payload.people:
        pid = item.id or str(uuid.uuid4())
        p = Person(
            id=pid,
            platform_username=item.platform_username,
            full_name=item.full_name,
            image_url=item.image_url,
            contact_details=[d.dict() for d in item.contact_details] if item.contact_details else [],
            website=item.website,
            content_count=item.content_count,
            follower_count=item.follower_count,
            following_count=item.following_count,
            introduction=item.introduction,
            is_verified=item.is_verified,
            category=item.category,
            job_title=item.job_title
        )
        db.add(p)
        created.append(pid)
    db.commit()
    return {"data": {"created": created}}
