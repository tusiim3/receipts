import json
from typing import Any, List, Optional

import google.generativeai as genai

from config import GEMINI_API_KEY, parse_json_response

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-pro"

TOS_PROMPT = """You are a financial consumer protection assistant. Analyze the following Terms of Service or User Agreement document.

Extract every clause that could result in unexpected financial cost to the user. Focus specifically on:
1. Auto-renewal terms (when, at what price, how to cancel)
2. Free trial conversion (exact date it converts, what it converts to)
3. Price increase clauses (can the company raise prices without notice?)
4. Cancellation friction (is cancellation hard? Phone only? Notice period required?)
5. Hidden fees (setup fees, early termination fees, overage charges)
6. Jurisdiction issues (dispute resolution only in a foreign country or via arbitration?)
7. Data monetization that has financial implications

For each finding return a JSON array where each object has:
- flag_title: string (short, clear title)
- severity: "high" | "medium" | "low"
- explanation: string (plain English, 1-2 sentences, what this means for the user)
- exact_quote: string (the relevant excerpt from the document, or null if not extractable)
- category: string (one of: auto_renewal, trial_conversion, price_increase, cancellation, hidden_fees, jurisdiction, data_monetization, other)

Return ONLY a valid JSON array. No explanation. No markdown.

Document:
{document_content}"""

GMAIL_EXTRACTION_PROMPT = """You are a financial intelligence assistant analyzing email data.

Below are emails from a user's Gmail inbox. Extract every subscription, recurring payment, or trial that involves money.

For each one return a JSON array where each object has:
- service_name: string (e.g. "Netflix", "Spotify", "AWS")
- amount: number (in whatever currency appears, null if not found)
- currency: string (e.g. "USD", "UGX", null if not found)
- frequency: string — one of "monthly", "annual", "weekly", "one-time", "unknown"
- last_charge_date: string ISO date or null
- trial_end_date: string ISO date or null (only if this is a trial)
- is_trial: boolean
- source_email_subject: string

Return ONLY a valid JSON array. No explanation. No markdown.

Emails:
{email_batch}"""

ALTERNATIVES_PROMPT = """The user currently pays {amount} {currency} per {frequency} for {service_name}.

Search for current cheaper alternatives to {service_name} available in 2025/2026.
Focus on alternatives that:
- Cost less than {amount} {currency} per month
- Are available internationally or specifically in East Africa/Uganda
- Have comparable core features

Return a JSON array of up to 3 alternatives, each with:
- name: string
- estimated_monthly_cost: string (e.g. "Free", "$4.99/month", "UGX 15,000/month")
- key_difference: string (one sentence)
- source_url: string (where you found this information)

Return ONLY valid JSON. No markdown."""

SENTIMENT_PROMPT = """Search for recent user reviews, complaints, and feedback about {service_name} subscription service.
Focus on: cancellation experience, billing surprises, customer support quality, and overall value.

Summarize in 2-3 sentences what users are generally saying. Be specific and honest.
Mention the sources (Reddit, Trustpilot, App Store, etc.) where you found this.

Return a JSON object with:
- sentiment: "positive" | "mixed" | "negative"
- summary: string (2-3 sentences)
- sources: array of strings

Return ONLY valid JSON. No markdown."""


def _get_model(tools: Optional[List] = None):
    if tools:
        return genai.GenerativeModel(MODEL_NAME, tools=tools)
    return genai.GenerativeModel(MODEL_NAME)


def _generate(prompt: str, tools: Optional[List] = None) -> str:
    model = _get_model(tools)
    response = model.generate_content(prompt)
    return response.text


def analyze_tos_text(content: str) -> list[dict]:
    prompt = TOS_PROMPT.format(document_content=content[:100000])
    text = _generate(prompt)
    return parse_json_response(text)


def analyze_tos_image(image_bytes: bytes, mime_type: str) -> list[dict]:
    model = _get_model()
    image_part = {"mime_type": mime_type, "data": image_bytes}
    prompt = TOS_PROMPT.format(document_content="[See attached image of Terms of Service document]")
    response = model.generate_content([prompt, image_part])
    return parse_json_response(response.text)


def extract_subscriptions(email_batch: str) -> list[dict]:
    prompt = GMAIL_EXTRACTION_PROMPT.format(email_batch=email_batch)
    text = _generate(prompt)
    result = parse_json_response(text)
    if isinstance(result, dict):
        return result.get("subscriptions", [])
    return result


def get_alternatives(service_name: str, amount: float, currency: str, frequency: str) -> list[dict]:
    prompt = ALTERNATIVES_PROMPT.format(
        service_name=service_name,
        amount=amount,
        currency=currency,
        frequency=frequency,
    )
    tools = [{"google_search": {}}]
    text = _generate(prompt, tools=tools)
    return parse_json_response(text)


def get_sentiment(service_name: str) -> dict:
    prompt = SENTIMENT_PROMPT.format(service_name=service_name)
    tools = [{"google_search": {}}]
    text = _generate(prompt, tools=tools)
    return parse_json_response(text)
