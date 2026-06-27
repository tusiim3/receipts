import base64
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI
from services import supabase_service

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SEARCH_QUERY = (
    'subject:(receipt OR invoice OR subscription OR "payment confirmation" OR '
    '"free trial" OR "billing" OR "charged") newer_than:12m'
)


def _client_config() -> dict:
    return {
        "web": {
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GMAIL_REDIRECT_URI],
        }
    }


def get_oauth_flow(state: Optional[str] = None) -> Flow:
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = GMAIL_REDIRECT_URI
    return flow


def get_authorization_url(state: str) -> str:
    flow = get_oauth_flow(state=state)
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return url


def exchange_code_for_tokens(code: str, state: str) -> dict:
    flow = get_oauth_flow(state=state)
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


def _build_credentials(token_data: dict) -> Credentials:
    expiry = None
    if token_data.get("expiry"):
        expiry = datetime.fromisoformat(token_data["expiry"])

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id", GMAIL_CLIENT_ID),
        client_secret=token_data.get("client_secret", GMAIL_CLIENT_SECRET),
        scopes=token_data.get("scopes", SCOPES),
        expiry=expiry,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        token_data["expiry"] = creds.expiry.isoformat() if creds.expiry else None

    return creds


def get_gmail_service(uid: str):
    token_data = supabase_service.get_gmail_tokens(uid)
    if not token_data:
        raise ValueError("Gmail not connected")

    creds = _build_credentials(token_data)

    if creds.token != token_data.get("token"):
        supabase_service.save_gmail_tokens(uid, {
            **token_data,
            "token": creds.token,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        })

    return build("gmail", "v1", credentials=creds)


def _decode_body(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_body(payload: dict) -> str:
    if not payload:
        return ""

    if payload.get("body", {}).get("data"):
        return _decode_body(payload["body"]["data"])

    parts = payload.get("parts", [])
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            return _decode_body(part["body"]["data"])
        if part.get("parts"):
            nested = _extract_body(part)
            if nested:
                return nested

    for part in parts:
        if part.get("body", {}).get("data"):
            return _decode_body(part["body"]["data"])

    return ""


def _get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def fetch_emails(uid: str, max_results: int = 200) -> list[dict[str, Any]]:
    service = get_gmail_service(uid)
    results = service.users().messages().list(
        userId="me",
        q=SEARCH_QUERY,
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        sender = _get_header(headers, "From")
        subject = _get_header(headers, "Subject")
        date_str = _get_header(headers, "Date")
        snippet = msg.get("snippet", "")
        body = _extract_body(msg.get("payload", {}))

        date_iso = None
        if date_str:
            try:
                date_iso = parsedate_to_datetime(date_str).isoformat()
            except Exception:
                date_iso = date_str

        emails.append({
            "sender": sender,
            "subject": subject,
            "date": date_iso,
            "snippet": snippet,
            "body": body[:2000] if body else snippet,
        })

    return emails


def format_email_batch(emails: list[dict]) -> str:
    lines = []
    for i, email in enumerate(emails, 1):
        lines.append(f"--- Email {i} ---")
        lines.append(f"From: {email.get('sender', '')}")
        lines.append(f"Subject: {email.get('subject', '')}")
        lines.append(f"Date: {email.get('date', '')}")
        lines.append(f"Body: {email.get('body', email.get('snippet', ''))}")
        lines.append("")
    return "\n".join(lines)
