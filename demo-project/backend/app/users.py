from fastapi import APIRouter

router = APIRouter()


@router.get("/api/users")
def list_users():
    return [{"id": "u-demo", "name": "Demo User"}]


def validate_user_permission():
    return True

