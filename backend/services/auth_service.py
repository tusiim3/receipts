from fastapi import HTTPException, Request
import jwt

from config import SUPABASE_JWT_SECRET


def verify_supabase_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
    )
    user_metadata = payload.get("user_metadata", {}) or {}
    return {
        "uid": payload["sub"],
        "email": payload.get("email", ""),
        "name": user_metadata.get("full_name") or user_metadata.get("name"),
    }


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
        return verify_supabase_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail={
            "error": True,
            "message": "Invalid or expired token",
            "code": "UNAUTHORIZED",
        })
