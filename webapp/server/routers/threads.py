import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.thread import Thread

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/threads")
def get_threads(action_id: int | None = None, is_confirmed: bool = True, generate_replies: bool = False, db: Session = Depends(get_db)):
    items = db.query(Thread).all()
    threads = []
    for t in items:
        threads.append({
            "socialUserId": t.socialUserId,
            "metadata": t.meta or {},
            "messages": t.messages or []
        })
    return {"threads": threads}

@router.put("/threads")
def upsert_threads(payload: dict, db: Session = Depends(get_db)):
    threads_payload = payload.get("threads") or []
    for tp in threads_payload:
        social_user_id = tp.get("socialUserId")
        messages = tp.get("messages") or []
        metadata = tp.get("metadata") or {}
        # Try to find by socialUserId
        t = db.query(Thread).filter(Thread.socialUserId == social_user_id).first()
        if not t:
            t = Thread(id=str(uuid.uuid4()), socialUserId=social_user_id, meta=metadata, messages=messages)
            db.add(t)
        else:
            t.meta = metadata
            t.messages = messages
    db.commit()
    return {"message": "Successful"}
