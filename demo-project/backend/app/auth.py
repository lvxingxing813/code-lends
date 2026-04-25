from fastapi import APIRouter

router = APIRouter()


@router.post("/api/login")
def login():
    return {"token": "demo"}


def check_permission():
    return True

