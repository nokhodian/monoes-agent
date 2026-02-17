from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.template import Template

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/templates/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(Template).get(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return {"data": {"template": {
        "id": t.id,
        "name": t.name,
        "subject": t.subject,
        "body": t.body,
        "metadata": t.meta or {}
    }}}
