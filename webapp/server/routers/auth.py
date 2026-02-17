from fastapi import APIRouter

router = APIRouter()

@router.post("/auth/login")
def login():
    return {"token": "dev-token"}
