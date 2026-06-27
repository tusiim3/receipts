import io
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PyPDF2 import PdfReader

from models.schemas import TosAnalysisRequest, TosFlag
from services import firestore_service, gemini_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/tos", tags=["tos"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def _build_risk_summary(flags: list[dict]) -> str:
    high_count = sum(1 for f in flags if f.get("severity") == "high")
    medium_count = sum(1 for f in flags if f.get("severity") == "medium")
    if high_count > 0:
        return f"This agreement has {high_count} high-risk financial clause{'s' if high_count != 1 else ''}. Review before signing."
    if medium_count > 0:
        return f"This agreement has {medium_count} medium-risk clause{'s' if medium_count != 1 else ''}. Worth reviewing carefully."
    if flags:
        return f"This agreement has {len(flags)} low-risk item{'s' if len(flags) != 1 else ''} to note."
    return "No significant financial risk clauses were found in this document."


def _save_and_return(uid: str, flags: list[dict], source: str):
    risk_summary = _build_risk_summary(flags)
    analyzed_at = datetime.now(timezone.utc).isoformat()

    analysis = {
        "flags": flags,
        "risk_summary": risk_summary,
        "source": source,
        "analyzed_at": analyzed_at,
    }
    analysis_id = firestore_service.save_tos_analysis(uid, analysis)

    return {
        "id": analysis_id,
        "flags": [TosFlag(**f) for f in flags],
        "risk_summary": risk_summary,
        "source": source,
        "analyzed_at": analyzed_at,
    }


@router.post("/analyze-url")
async def analyze_url(body: TosAnalysisRequest, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(body.url)
            response.raise_for_status()
            html = response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Failed to fetch URL: {str(e)}",
            "code": "URL_FETCH_ERROR",
        })

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)

    if len(text) < 100:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": "Could not extract enough text from the URL",
            "code": "INSUFFICIENT_CONTENT",
        })

    try:
        flags = gemini_service.analyze_tos_text(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": True,
            "message": f"Failed to analyze document: {str(e)}",
            "code": "GEMINI_PARSE_ERROR",
        })

    return _save_and_return(user["uid"], flags, body.url)


@router.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    filename = file.filename or "upload"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            "code": "INVALID_FILE_TYPE",
        })

    content = await file.read()

    try:
        if ext == ".pdf":
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)

            if len(text.strip()) >= 100:
                flags = gemini_service.analyze_tos_text(text)
            else:
                flags = gemini_service.analyze_tos_image(content, "application/pdf")
        else:
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(ext, file.content_type or "image/png")
            flags = gemini_service.analyze_tos_image(content, mime_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": True,
            "message": f"Failed to analyze file: {str(e)}",
            "code": "GEMINI_PARSE_ERROR",
        })

    return _save_and_return(user["uid"], flags, filename)
