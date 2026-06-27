from fastapi import APIRouter, Depends

from models.schemas import UserProfile
from services import firestore_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(user: dict = Depends(get_current_user)):
    profile = firestore_service.create_user_if_not_exists(
        uid=user["uid"],
        email=user.get("email", ""),
        display_name=user.get("name"),
    )
    return {"user": profile}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    profile = firestore_service.create_user_if_not_exists(
        uid=user["uid"],
        email=user.get("email", ""),
        display_name=user.get("name"),
    )
    return UserProfile(**profile)
