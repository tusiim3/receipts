from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import AlternativesRequest, SentimentRequest
from services import firestore_service, gemini_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def _normalize_to_monthly(amount: Optional[float], frequency: str) -> float:
    if amount is None:
        return 0.0
    freq = (frequency or "unknown").lower()
    if freq == "annual":
        return amount / 12
    if freq == "weekly":
        return amount * 4.33
    if freq == "one-time":
        return 0.0
    return amount


def _compute_wasteful_flags(subscriptions: list[dict], tos_analyses: list[dict]) -> list[dict]:
    flags = []

    category_groups: dict[str, list[str]] = {}
    for sub in subscriptions:
        cat = sub.get("category", "other")
        name = sub.get("service_name", "")
        category_groups.setdefault(cat, []).append(name)

    for cat, services in category_groups.items():
        if len(services) > 1 and cat not in ("other", "utilities"):
            flags.append({
                "type": "duplicate_category",
                "message": f"You have {len(services)} {cat.replace('_', ' ')} subscriptions",
                "services": services,
            })

    now = datetime.now(timezone.utc)
    for sub in subscriptions:
        if sub.get("is_trial") and sub.get("trial_end_date"):
            try:
                trial_end = datetime.fromisoformat(sub["trial_end_date"].replace("Z", "+00:00"))
                if trial_end.tzinfo is None:
                    trial_end = trial_end.replace(tzinfo=timezone.utc)
                days_left = (trial_end - now).days
                if 0 <= days_left <= 7:
                    flags.append({
                        "type": "trial_ending",
                        "message": f"{sub['service_name']} trial ends in {days_left} day{'s' if days_left != 1 else ''}",
                        "services": [sub["service_name"]],
                    })
            except Exception:
                pass

        last_charge = sub.get("last_charge_date")
        if last_charge:
            try:
                charge_date = datetime.fromisoformat(last_charge.replace("Z", "+00:00"))
                if charge_date.tzinfo is None:
                    charge_date = charge_date.replace(tzinfo=timezone.utc)
                if (now - charge_date).days >= 90:
                    flags.append({
                        "type": "possibly_forgotten",
                        "message": f"{sub['service_name']} — no charge in 90+ days",
                        "services": [sub["service_name"]],
                    })
            except Exception:
                pass

    high_risk_services = set()
    for analysis in tos_analyses:
        for flag in analysis.get("flags", []):
            if flag.get("severity") == "high":
                source = analysis.get("source", "")
                high_risk_services.add(source)

    for sub in subscriptions:
        name = sub.get("service_name", "")
        for analysis in tos_analyses:
            source = analysis.get("source", "").lower()
            if name.lower() in source or source in name.lower():
                high_flags = [f for f in analysis.get("flags", []) if f.get("severity") == "high"]
                if high_flags:
                    flags.append({
                        "type": "high_risk_tos",
                        "message": f"{name} has high-risk terms of service clauses",
                        "services": [name],
                    })
                break

    return flags


@router.get("/summary")
async def get_summary(user: dict = Depends(get_current_user)):
    uid = user["uid"]
    subscriptions = firestore_service.get_subscriptions(uid)
    tos_analyses = firestore_service.get_tos_analyses(uid)

    total_monthly = sum(
        _normalize_to_monthly(sub.get("amount"), sub.get("frequency", "unknown"))
        for sub in subscriptions
    )

    currency = "USD"
    for sub in subscriptions:
        if sub.get("currency"):
            currency = sub["currency"]
            break

    grouped: dict[str, list] = {}
    for sub in subscriptions:
        cat = sub.get("category", "other")
        grouped.setdefault(cat, []).append(sub)

    wasteful_flags = _compute_wasteful_flags(subscriptions, tos_analyses)

    return {
        "subscriptions": subscriptions,
        "total_monthly_spend": round(total_monthly, 2),
        "currency": currency,
        "grouped_by_category": grouped,
        "wasteful_flags": wasteful_flags,
        "tos_analyses": tos_analyses,
    }


@router.post("/alternatives")
async def get_alternatives(body: AlternativesRequest, user: dict = Depends(get_current_user)):
    try:
        alternatives = gemini_service.get_alternatives(
            service_name=body.service_name,
            amount=body.current_amount,
            currency=body.currency,
            frequency=body.frequency,
        )
        return {"alternatives": alternatives}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": True,
            "message": f"Failed to get alternatives: {str(e)}",
            "code": "GEMINI_PARSE_ERROR",
        })


@router.post("/sentiment")
async def get_sentiment(body: SentimentRequest, user: dict = Depends(get_current_user)):
    try:
        sentiment = gemini_service.get_sentiment(body.service_name)
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": True,
            "message": f"Failed to get sentiment: {str(e)}",
            "code": "GEMINI_PARSE_ERROR",
        })
