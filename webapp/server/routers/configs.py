import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.config import ConfigEntry

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/configs/{full_config_name}")
def get_config(full_config_name: str, db: Session = Depends(get_db)):
    c = db.query(ConfigEntry).get(full_config_name)
    if not c:
        return {"message": "NotFound", "data": None}
    return {"message": "Successful", "data": c.data}

@router.post("/configs/extracttest")
def extract_test(payload: dict):
    return [{"configName": payload.get("configName"), "score": 0.95}]

@router.post("/configs/generate")
def generate_config(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("configName")
    schema = payload.get("extractionSchema") or {}
    data = {
        "configName": name,
        "purpose": payload.get("purpose"),
        "schema": schema,
        "xpath": {}
    }
    entry = ConfigEntry(name=name, data=data)
    db.merge(entry)
    db.commit()
    return {"message": "Successful", "data": data}

@router.get("/crawler/xpath")
def crawler_xpath(db: Session = Depends(get_db)):
    c = db.query(ConfigEntry).get("crawler_xpath")
    if c:
        return {"data": c.data}
    return {"data": {"xpath": {}, "settings": {}}}
