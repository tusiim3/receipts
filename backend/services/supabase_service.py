from datetime import datetime, timezone
from typing import Optional

from supabase import Client, create_client

from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Supabase credentials not configured")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client


def _profile_to_api(row: dict) -> dict:
    return {
        "uid": row["id"],
        "email": row.get("email", ""),
        "displayName": row.get("display_name", ""),
        "createdAt": row.get("created_at"),
    }


def create_user_if_not_exists(uid: str, email: str, display_name: Optional[str] = None) -> dict:
    client = get_client()
    result = client.table("profiles").select("*").eq("id", uid).execute()

    if result.data:
        return _profile_to_api(result.data[0])

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": uid,
        "email": email,
        "display_name": display_name or "",
        "created_at": now,
    }
    client.table("profiles").insert(row).execute()
    return {
        "uid": uid,
        "email": email,
        "displayName": display_name or "",
        "createdAt": now,
    }


def save_gmail_tokens(uid: str, tokens: dict):
    # TODO: encrypt at rest in production using Fernet/KMS
    client = get_client()
    client.table("gmail_tokens").upsert({
        "user_id": uid,
        "tokens": tokens,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def get_gmail_tokens(uid: str) -> Optional[dict]:
    client = get_client()
    result = client.table("gmail_tokens").select("tokens").eq("user_id", uid).execute()
    if result.data:
        return result.data[0]["tokens"]
    return None


def save_subscriptions(uid: str, subscriptions: list[dict]):
    client = get_client()
    client.table("subscriptions").delete().eq("user_id", uid).execute()

    if not subscriptions:
        return

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for sub in subscriptions:
        rows.append({
            "user_id": uid,
            "service_name": sub.get("service_name", ""),
            "amount": sub.get("amount"),
            "currency": sub.get("currency"),
            "frequency": sub.get("frequency", "unknown"),
            "last_charge_date": sub.get("last_charge_date"),
            "trial_end_date": sub.get("trial_end_date"),
            "is_trial": sub.get("is_trial", False),
            "source_email_subject": sub.get("source_email_subject"),
            "category": sub.get("category"),
            "updated_at": now,
        })
    client.table("subscriptions").insert(rows).execute()


def get_subscriptions(uid: str) -> list[dict]:
    client = get_client()
    result = client.table("subscriptions").select("*").eq("user_id", uid).execute()
    subs = []
    for row in result.data or []:
        subs.append({
            "service_name": row.get("service_name"),
            "amount": float(row["amount"]) if row.get("amount") is not None else None,
            "currency": row.get("currency"),
            "frequency": row.get("frequency", "unknown"),
            "last_charge_date": row.get("last_charge_date"),
            "trial_end_date": row.get("trial_end_date"),
            "is_trial": row.get("is_trial", False),
            "source_email_subject": row.get("source_email_subject"),
            "category": row.get("category"),
        })
    return subs


def save_tos_analysis(uid: str, analysis: dict) -> str:
    client = get_client()
    result = client.table("tos_analyses").insert({
        "user_id": uid,
        "flags": analysis["flags"],
        "risk_summary": analysis["risk_summary"],
        "source": analysis["source"],
        "analyzed_at": analysis["analyzed_at"],
    }).execute()
    return result.data[0]["id"]


def get_tos_analyses(uid: str) -> list[dict]:
    client = get_client()
    result = client.table("tos_analyses").select("*").eq("user_id", uid).execute()
    return [
        {
            "id": row["id"],
            "flags": row.get("flags", []),
            "risk_summary": row.get("risk_summary"),
            "source": row.get("source"),
            "analyzed_at": row.get("analyzed_at"),
        }
        for row in (result.data or [])
    ]


def get_cached_category(service_name: str) -> Optional[str]:
    client = get_client()
    normalized = service_name.lower().strip()
    result = client.table("category_cache").select("category").eq("service_name_key", normalized).execute()
    if result.data:
        return result.data[0]["category"]
    return None


def cache_category(service_name: str, category: str):
    client = get_client()
    normalized = service_name.lower().strip()
    client.table("category_cache").upsert({
        "service_name_key": normalized,
        "service_name": service_name,
        "category": category,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
