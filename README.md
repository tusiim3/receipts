# Receipts

Receipts helps you understand and optimize your recurring financial commitments. It connects two intelligence inputs — your inbox and the fine print — into one cost intelligence dashboard.

## What it does

### Gmail Scanner

Connects to Gmail via OAuth and scans for subscription confirmations, receipts, trial notices, and billing emails. It extracts what you're paying, to whom, and how often, then categorizes each service (streaming, productivity, food delivery, etc.).

### Terms of Service Analyzer

Paste a URL, upload a PDF, or share a screenshot of any terms of service or user agreement. Receipts flags financial traps before you commit — auto-renewal clauses, free trial conversions, hidden fees, cancellation friction, price increase terms, and more. Each finding includes a severity rating and a plain-English explanation.

### Cost Intelligence Dashboard

The dashboard pulls together everything from Gmail scans and ToS analyses:

- **Subscription map** — full view of active subscriptions grouped by category, with estimated monthly spend
- **Wasteful spend flags** — duplicate categories, trials ending soon, subscriptions with no recent charges, high-risk ToS matches
- **Alternatives & savings** — AI-suggested cheaper alternatives with live search grounding
- **Platform sentiment** — synthesized user feedback on cancellation experience, billing surprises, and support quality

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), TailwindCSS |
| Backend | FastAPI (Python) |
| Database | Firestore |
| Auth | Firebase Authentication |
| AI | Gemini 1.5 Pro, Featherless AI (Mistral-7B) |
| Email | Gmail API (OAuth 2.0, read-only) |

## Project structure

```
├── frontend/          React app (auth, dashboard, Gmail, ToS, intelligence)
├── backend/           FastAPI API (routers, services, models)
├── docker-compose.yml Local development with Docker
└── deploy.sh          Cloud Run deployment (WIP)
```
