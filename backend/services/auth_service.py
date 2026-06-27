from fastapi import Depends, HTTPException, Request
from firebase_admin import auth


def verify_firebase_token(token: str) -> dict:
    return auth.verify_id_token(token)


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={
            "error": True,
            "message": "Missing or invalid authorization header",
            "code": "UNAUTHORIZED",
        })

    token = auth_header.split("Bearer ", 1)[1]
    try:
        decoded = auth.verify_id_token(token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "name": decoded.get("name"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail={
            "error": True,
            "message": "Invalid or expired token",
            "code": "UNAUTHORIZED",
        })
