import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, engine, Base
from ..models.action_target import ActionTarget

Base.metadata.create_all(bind=engine)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/action-targets")
def list_action_targets(actionId: str | None = None, status: str | None = None, platform: str | None = None, first: int = 100, after: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ActionTarget)
    if actionId:
        query = query.filter(ActionTarget.actionId == actionId)
    if status:
        query = query.filter(ActionTarget.status == status)
    if platform:
        query = query.filter(ActionTarget.platform == platform)
    if after:
        # Simple cursor: skip items until id > after (lexicographic for UUID)
        query = query.filter(ActionTarget.id > after)
    items = query.order_by(ActionTarget.id).limit(first).all()
    nodes = []
    for t in items:
        nodes.append({
            "id": t.id,
            "actionId": t.actionId,
            "personId": t.personId,
            "platform": t.platform,
            "link": t.link,
            "sourceType": t.sourceType,
            "status": t.status,
            "lastInteractedAt": t.lastInteractedAt,
            "commentText": t.commentText,
            "metadata": t.meta or {}
        })
    end_cursor = nodes[-1]["id"] if nodes else None
    # Check if more after end_cursor
    has_next = False
    if end_cursor:
        has_next = db.query(ActionTarget).filter(ActionTarget.id > end_cursor).count() > 0
    return {"data": {"actionTargets": nodes, "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor}}}

@router.get("/actions/{id}/targets")
def get_action_targets(id: str, db: Session = Depends(get_db)):
    items = db.query(ActionTarget).filter(ActionTarget.actionId == id).all()
    nodes = []
    for t in items:
        nodes.append({
            "id": t.id,
            "actionId": t.actionId,
            "personId": t.personId,
            "platform": t.platform,
            "link": t.link,
            "sourceType": t.sourceType,
            "status": t.status,
            "lastInteractedAt": t.lastInteractedAt,
            "commentText": t.commentText,
            "metadata": t.metadata or {}
        })
    return {"data": {"actionTargets": nodes}}

@router.post("/actions/{id}/targets")
def add_targets(id: str, payload: dict, db: Session = Depends(get_db)):
    targets = payload.get("targets") or []
    created = []
    for t in targets:
        tid = str(uuid.uuid4())
        at = ActionTarget(
            id=tid,
            actionId=id,
            personId=t.get("personId") or "",
            platform=t.get("platform") or "",
            link=t.get("link") or "",
            sourceType=t.get("sourceType") or "PROFILE",
            status="PENDING",
            lastInteractedAt=None,
            commentText=t.get("commentText"),
            meta=t.get("metadata") or {}
        )
        db.add(at)
        created.append(tid)
    db.commit()
    return {"data": {"created": created}}

@router.patch("/action-targets/{id}")
def patch_target(id: str, payload: dict, db: Session = Depends(get_db)):
    t = db.query(ActionTarget).get(id)
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.items():
        setattr(t, k, v)
    db.commit()
    return {"message": "updated"}
