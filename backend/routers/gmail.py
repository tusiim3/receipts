import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from config import FRONTEND_URL
from services import supabase_service, gemini_service
from services.auth_service import get_current_user, verify_supabase_token
from services import gmail_service, featherless_service

router = APIRouter(tags=["gmail"])

_oauth_states: dict[str, str] = {}


@router.get("/auth/gmail")
async def gmail_auth(token: str = Query(...)):
    try:
        decoded = verify_supabase_token(token)
        uid = decoded["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail={
            "error": True,
            "message": "Invalid auth token",
            "code": "UNAUTHORIZED",
        })

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = uid

    auth_url = gmail_service.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/auth/gmail/callback")
async def gmail_callback(code: str = Query(...), state: str = Query(...)):
    uid = _oauth_states.pop(state, None)
    if not uid:
        return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error=invalid_state")

    try:
        tokens = gmail_service.exchange_code_for_tokens(code, state)
        supabase_service.save_gmail_tokens(uid, tokens)
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error={str(e)}")

    return RedirectResponse(url=f"{FRONTEND_URL}/gmail?connected=true")


@router.post("/gmail/scan")
async def scan_gmail(user: dict = Depends(get_current_user)):
    uid = user["uid"]

    try:
        emails = gmail_service.fetch_emails(uid, max_results=200)
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": "Gmail not connected. Please connect Gmail first.",
            "code": "GMAIL_NOT_CONNECTED",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": True,
            "message": f"Failed to fetch emails: {str(e)}",
            "code": "GMAIL_FETCH_ERROR",
        })

    all_subscriptions: list[dict] = []
    batch_size = 20

    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        email_text = gmail_service.format_email_batch(batch)
        try:
            extracted = gemini_service.extract_subscriptions(email_text)
            if isinstance(extracted, list):
                all_subscriptions.extend(extracted)
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "error": True,
                "message": f"Failed to extract subscriptions: {str(e)}",
                "code": "GEMINI_PARSE_ERROR",
            })

    deduped: dict[str, dict] = {}
    for sub in all_subscriptions:
        name = sub.get("service_name", "").strip()
        if not name:
            continue
        existing = deduped.get(name.lower())
        if not existing:
            deduped[name.lower()] = sub
        else:
            new_date = sub.get("last_charge_date") or ""
            old_date = existing.get("last_charge_date") or ""
            if new_date > old_date:
                deduped[name.lower()] = sub

    subscriptions = list(deduped.values())

    for sub in subscriptions:
        try:
            sub["category"] = featherless_service.categorize(sub["service_name"])
        except Exception:
            sub["category"] = "other"

    supabase_service.save_subscriptions(uid, subscriptions)

    unique_services = len(set(s.get("service_name", "").lower() for s in subscriptions))

    return {
        "subscriptions": subscriptions,
        "total_count": len(subscriptions),
        "unique_services": unique_services,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
