import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.action import Action
from ..schemas.action import ActionDTO, CreateActionDTO, PatchActionDTO, PatchStateDTO
from ..models.action_target import ActionTarget
from ..models.person import Person

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/actions")
def list_actions(state: str | None = None, type: str | None = None, targetPlatform: str | None = None, disabled: bool | None = None, ownerId: str | None = None, q: str | None = None, page: int = 1, perPage: int = 20, sort: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Action)
    if state:
        query = query.filter(Action.state == state)
    if type:
        query = query.filter(Action.type == type)
    if targetPlatform:
        query = query.filter(Action.targetPlatform == targetPlatform)
    if disabled is not None:
        query = query.filter(Action.disabled == disabled)
    if ownerId:
        query = query.filter(Action.ownerId == ownerId)
    if q:
        query = query.filter(Action.title.ilike(f"%{q}%"))
    total = query.count()
    items = query.offset((page - 1) * perPage).limit(perPage).all()
    data = []
    for a in items:
        data.append({
            "id": a.id,
            "createdAt": a.createdAt,
            "createdBy": a.createdBy,
            "ownerId": a.ownerId,
            "title": a.title,
            "type": a.type,
            "state": a.state,
            "disabled": a.disabled,
            "targetPlatform": a.targetPlatform,
            "position": a.position,
            "cost": a.cost,
            "actionExecutionCount": a.actionExecutionCount,
            "contentSubject": a.contentSubject,
            "contentMessage": a.contentMessage,
            "contentBlobURL": a.contentBlobURL or [],
            "scheduledDate": a.scheduledDate,
            "executionInterval": a.executionInterval,
            "startDate": a.startDate,
            "endDate": a.endDate,
            "campaignID": a.campaignID,
            "actionTarget": None
        })
    return {"data": {"actions": data, "totalCount": total}}

@router.get("/actions/{id}")
def get_action(id: str, db: Session = Depends(get_db)):
    a = db.query(Action).get(id)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    return {"data": {"action": {
        "id": a.id,
        "createdAt": a.createdAt,
        "createdBy": a.createdBy,
        "ownerId": a.ownerId,
        "title": a.title,
        "type": a.type,
        "state": a.state,
        "disabled": a.disabled,
        "targetPlatform": a.targetPlatform,
        "position": a.position,
        "cost": a.cost,
        "actionExecutionCount": a.actionExecutionCount,
        "contentSubject": a.contentSubject,
        "contentMessage": a.contentMessage,
        "contentBlobURL": a.contentBlobURL or [],
        "scheduledDate": a.scheduledDate,
        "executionInterval": a.executionInterval,
        "startDate": a.startDate,
        "endDate": a.endDate,
        "campaignID": a.campaignID
    }}}

@router.post("/actions")
def create_action(payload: CreateActionDTO, db: Session = Depends(get_db)):
    action_id = str(uuid.uuid4())
    a = Action(
        id=action_id,
        createdAt=0,
        createdBy=payload.createdBy,
        ownerId=payload.ownerId,
        title=payload.title,
        type=payload.type,
        state=payload.state,
        disabled=False,
        targetPlatform=payload.targetPlatform,
        position=0,
        cost=0,
        actionExecutionCount=0,
        contentSubject=payload.contentSubject,
        contentMessage=payload.contentMessage,
        contentBlobURL=payload.contentBlobURL,
        scheduledDate=payload.scheduledDate,
        executionInterval=payload.executionInterval,
        startDate=payload.startDate,
        endDate=payload.endDate,
        campaignID=payload.campaignID
    )
    db.add(a)
    db.commit()
    return {"data": {"id": action_id}}

@router.patch("/actions/{id}")
def patch_action(id: str, payload: PatchActionDTO, db: Session = Depends(get_db)):
    a = db.query(Action).get(id)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    return {"message": "updated"}

@router.patch("/actions/{id}/state")
def patch_action_state(id: str, payload: PatchStateDTO, db: Session = Depends(get_db)):
    a = db.query(Action).get(id)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    a.state = payload.state
    if payload.state == "DONE":
        a.disabled = False
    db.commit()
    return {"message": "state updated"}

@router.get("/actions/summary")
def actions_summary(db: Session = Depends(get_db)):
    counts = {"ALL": 0, "PENDING": 0, "IN_PROGRESS": 0, "DONE": 0}
    counts["ALL"] = db.query(Action).count()
    counts["PENDING"] = db.query(Action).filter(Action.state == "PENDING").count()
    counts["IN_PROGRESS"] = db.query(Action).filter(Action.state == "INPROGRESS").count()
    counts["DONE"] = db.query(Action).filter(Action.state == "DONE").count()
    return counts

@router.get("/actions/{id}/collected")
def get_action_collected(id: str, db: Session = Depends(get_db)):
    targets = db.query(ActionTarget).filter(ActionTarget.actionId == id).all()
    people_map = {}
    items = []
    for t in targets:
        if t.personId and t.personId not in people_map:
            p = db.query(Person).get(t.personId)
            people_map[t.personId] = p
        p = people_map.get(t.personId)
        item = {
            "id": t.personId,
            "platform_username": p.platform_username if p else "",
            "full_name": p.full_name if p else "",
            "image_url": p.image_url if p else "",
            "contact_details": p.contact_details if p and p.contact_details else [],
            "website": p.website if p else "",
            "content_count": p.content_count if p else 0,
            "follower_count": p.follower_count if p else 0,
            "following_count": p.following_count if p else 0,
            "introduction": p.introduction if p else "",
            "is_verified": p.is_verified if p else False,
            "category": p.category if p else "",
            "job_title": p.job_title if p else "",
            "platform": t.platform.lower(),
            "link": t.link,
            "status": t.status
        }
        items.append(item)
    return {"data": {"collected": items, "totalCount": len(items)}}
