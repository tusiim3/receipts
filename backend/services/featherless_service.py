from openai import OpenAI

from config import FEATHERLESS_API_KEY
from services import firestore_service

FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"
MODEL = "Mistral-7B-Instruct"

CATEGORIZE_PROMPT = """Categorize the following subscription service into exactly one of these categories:
streaming, music, productivity, cloud_storage, gaming, food_delivery, fitness, news, education, finance, communication, utilities, other

Service name: {service_name}

Return only the category word. Nothing else."""

VALID_CATEGORIES = {
    "streaming", "music", "productivity", "cloud_storage", "gaming",
    "food_delivery", "fitness", "news", "education", "finance",
    "communication", "utilities", "other",
}


def _get_client() -> OpenAI:
    return OpenAI(base_url=FEATHERLESS_BASE_URL, api_key=FEATHERLESS_API_KEY)


def categorize(service_name: str) -> str:
    cached = firestore_service.get_cached_category(service_name)
    if cached:
        return cached

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": CATEGORIZE_PROMPT.format(service_name=service_name)}],
        max_tokens=20,
        temperature=0,
    )
    category = response.choices[0].message.content.strip().lower()
    if category not in VALID_CATEGORIES:
        category = "other"

    firestore_service.cache_category(service_name, category)
    return category
