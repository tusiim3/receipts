import os
from datetime import datetime, timezone
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore, storage

from config import FIREBASE_PROJECT_ID, FIREBASE_STORAGE_BUCKET

_db = None
_bucket = None


def _get_credentials():
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")

    if not private_key or not client_email or not FIREBASE_PROJECT_ID:
        return None

    if private_key == "your_firebase_private_key_here":
        return None

    return credentials.Certificate({
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "private_key": private_key.replace("\\n", "\n"),
        "client_email": client_email,
        "token_uri": "https://oauth2.googleapis.com/token",
    })


def init_firebase():
    global _db, _bucket
    if not firebase_admin._apps:
        cred = _get_credentials()
        if cred is None:
            raise RuntimeError("Firebase credentials not configured")
        firebase_admin.initialize_app(cred, {
            "storageBucket": FIREBASE_STORAGE_BUCKET or None,
        })
    _db = firestore.client()
    if FIREBASE_STORAGE_BUCKET:
        _bucket = storage.bucket()
    return _db


def get_db():
    if _db is None:
        init_firebase()
    return _db


def get_storage_bucket():
    if _db is None:
        init_firebase()
    return _bucket


def create_user_if_not_exists(uid: str, email: str, display_name: Optional[str] = None):
    db = get_db()
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    if not doc.exists:
        user_ref.set({
            "uid": uid,
            "email": email,
            "displayName": display_name or "",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
    return user_ref.get().to_dict()


def save_gmail_tokens(uid: str, tokens: dict):
    # TODO: encrypt at rest in production using Fernet/KMS
    db = get_db()
    db.collection("users").document(uid).collection("gmail_tokens").document("default").set({
        **tokens,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    })


def get_gmail_tokens(uid: str) -> Optional[dict]:
    db = get_db()
    doc = db.collection("users").document(uid).collection("gmail_tokens").document("default").get()
    return doc.to_dict() if doc.exists else None


def save_subscriptions(uid: str, subscriptions: list[dict]):
    db = get_db()
    batch = db.batch()
    subs_ref = db.collection("users").document(uid).collection("subscriptions")

    existing = {d.id: d for d in subs_ref.stream()}
    for doc_id in existing:
        batch.delete(subs_ref.document(doc_id))

    for i, sub in enumerate(subscriptions):
        doc_ref = subs_ref.document(str(i))
        batch.set(doc_ref, {**sub, "updatedAt": datetime.now(timezone.utc).isoformat()})

    batch.commit()


def get_subscriptions(uid: str) -> list[dict]:
    db = get_db()
    docs = db.collection("users").document(uid).collection("subscriptions").stream()
    return [d.to_dict() for d in docs]


def save_tos_analysis(uid: str, analysis: dict) -> str:
    db = get_db()
    doc_ref = db.collection("users").document(uid).collection("tos_analyses").document()
    doc_ref.set(analysis)
    return doc_ref.id


def get_tos_analyses(uid: str) -> list[dict]:
    db = get_db()
    docs = db.collection("users").document(uid).collection("tos_analyses").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]


def get_cached_category(service_name: str) -> Optional[str]:
    db = get_db()
    normalized = service_name.lower().strip()
    doc = db.collection("category_cache").document(normalized).get()
    return doc.to_dict().get("category") if doc.exists else None


def cache_category(service_name: str, category: str):
    db = get_db()
    normalized = service_name.lower().strip()
    db.collection("category_cache").document(normalized).set({
        "service_name": service_name,
        "category": category,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    })
