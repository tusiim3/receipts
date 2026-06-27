# Cursor Prompt — [ADD FUNNY NAME] Full Build

## Project Overview

Build a full-stack web application called **[ADD FUNNY NAME]** that helps users understand and optimize their recurring financial commitments. It has two core intelligence inputs and one output dashboard:

- **Gmail Scanner** — connects to the user's Gmail via OAuth, scans for subscription confirmations, receipts, and trial notices, and maps what they're paying, to whom, and how often.
- **Terms Analyzer** — accepts a URL, PDF upload, or screenshot image of any terms of service or user agreement, and extracts financial traps, auto-renewal clauses, hidden costs, and cancellation friction before the user commits.
- **Cost Intelligence Dashboard** — fed by both inputs. Shows the user's full subscription map, flags wasteful or forgotten spend, recommends cheaper alternatives using live Google Search grounding, and synthesizes public sentiment about each platform.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), TailwindCSS |
| Backend | FastAPI (Python) |
| Database | Firestore (Google Cloud) |
| Auth | Firebase Authentication (Email/Password + Google Sign-In) |
| AI — Primary | Gemini 1.5 Pro API (long context, multimodal, search grounding) |
| AI — Categorization | Featherless AI API (open source LLM inference) |
| Email Access | Gmail API (OAuth 2.0, `gmail.readonly` scope) |
| Hosting — Frontend | Cloud Run (containerized via Docker) |
| Hosting — Backend | Cloud Run (containerized via Docker) |
| File Storage | Firebase Storage (for uploaded PDFs and screenshots) |

---

## Environment Variables — Placeholders Only

Do not hardcode any keys. Use the following placeholders throughout. The developer will fill these in via a `.env` file and Cloud Run environment variable configuration.

```
# Backend (.env)
GEMINI_API_KEY=your_gemini_api_key_here
FEATHERLESS_API_KEY=your_featherless_api_key_here
GMAIL_CLIENT_ID=your_gmail_oauth_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_oauth_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback
FIREBASE_PROJECT_ID=your_firebase_project_id_here
FIREBASE_PRIVATE_KEY=your_firebase_private_key_here
FIREBASE_CLIENT_EMAIL=your_firebase_client_email_here
FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket_here

# Frontend (.env)
VITE_FIREBASE_API_KEY=your_firebase_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_firebase_project_id_here
VITE_FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket_here
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id_here
VITE_FIREBASE_APP_ID=your_firebase_app_id_here
VITE_API_BASE_URL=http://localhost:8000
```

---

## Project Structure

```
[add-funny-name]/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.jsx
│   │   │   │   └── SignupPage.jsx
│   │   │   ├── dashboard/
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── SubscriptionCard.jsx
│   │   │   │   └── SpendSummary.jsx
│   │   │   ├── gmail/
│   │   │   │   └── GmailConnect.jsx
│   │   │   ├── tos/
│   │   │   │   ├── TosAnalyzer.jsx
│   │   │   │   └── TosResultCard.jsx
│   │   │   └── intelligence/
│   │   │       └── CostIntelligencePage.jsx
│   │   ├── firebase.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── gmail.py
│   │   ├── tos.py
│   │   └── intelligence.py
│   ├── services/
│   │   ├── gemini_service.py
│   │   ├── featherless_service.py
│   │   ├── gmail_service.py
│   │   └── firestore_service.py
│   ├── models/
│   │   └── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
│
└── docker-compose.yml
```

---

## Authentication

Use **Firebase Authentication** for user management.

- Support Email/Password signup and login
- Support Google Sign-In (OAuth popup)
- On the frontend, use the Firebase JS SDK (`firebase/auth`)
- On the backend, verify Firebase ID tokens on every protected endpoint using the Firebase Admin SDK (`firebase-admin` Python package)
- Store a user document in Firestore under `users/{uid}` on first login containing: `uid`, `email`, `displayName`, `createdAt`
- Auth is important but not the priority — build it cleanly but keep it simple. No email verification, no password reset flow for now. Just login, signup, and Google Sign-In working end to end.
- Protect all backend routes except `/health` with a Firebase token verification middleware

---

## Feature 1: Gmail Scanner

### Frontend (`GmailConnect.jsx`)
- A button: "Connect Gmail"
- On click, redirect user to Gmail OAuth consent flow
- After successful OAuth, show a "Scanning your inbox..." loading state
- On completion, show a summary: "Found X subscriptions across Y services"
- List extracted subscriptions with service name, amount, frequency, and last charge date
- Each subscription has a category badge (streaming, productivity, food, etc.)

### Backend (`routers/gmail.py`, `services/gmail_service.py`)

**OAuth Flow:**
- `GET /auth/gmail` — generates Gmail OAuth URL with `gmail.readonly` scope and redirects user
- `GET /auth/gmail/callback` — handles OAuth callback, exchanges code for access + refresh tokens, stores tokens encrypted in Firestore under `users/{uid}/gmail_tokens`

**Scanning:**
- `POST /gmail/scan` — authenticated endpoint
  - Fetches emails from Gmail API using stored tokens
  - Search query: `subject:(receipt OR invoice OR subscription OR "payment confirmation" OR "free trial" OR "billing" OR "charged") newer_than:12m`
  - Fetch up to 200 matching emails, extract: sender, subject, date, snippet, and full body for relevant ones
  - Pass batches of emails to Gemini for extraction (see Gemini service below)
  - Pass extracted subscriptions to Featherless for categorization (see Featherless service below)
  - Store results in Firestore under `users/{uid}/subscriptions`
  - Return structured subscription list to frontend

### Gemini Service — Gmail Extraction (`services/gemini_service.py`)

Use `gemini-1.5-pro` via the Gemini API Python SDK (`google-generativeai`).

```python
# Prompt for Gmail extraction
"""
You are a financial intelligence assistant analyzing email data.

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
{email_batch}
"""
```

Batch emails in groups of 20 to stay within context limits. Deduplicate by `service_name` after all batches complete, keeping the most recent entry per service.

### Featherless Service — Categorization (`services/featherless_service.py`)

Use **Mistral-7B-Instruct** via Featherless AI. Featherless uses an OpenAI-compatible API so use the `openai` Python SDK pointed at Featherless's base URL.

**Justification for model choice:** Categorization is a lightweight classification task — mapping a service name to a category. It does not need Gemini's long context or multimodal capabilities. Mistral-7B-Instruct on Featherless handles this faster and cheaper, preserving Gemini API quota for the heavier tasks.

```python
# Featherless base URL
FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"

# Prompt for categorization
"""
Categorize the following subscription service into exactly one of these categories:
streaming, music, productivity, cloud_storage, gaming, food_delivery, fitness, news, education, finance, communication, utilities, other

Service name: {service_name}

Return only the category word. Nothing else.
"""
```

Call Featherless once per unique service name. Cache results in Firestore so repeat scans don't re-categorize known services.

---

## Feature 2: Terms of Service Analyzer

### Frontend (`tos/TosAnalyzer.jsx`)

Three input options on a single clean page:
1. **URL input** — text field, user pastes a link to any terms/signup page
2. **PDF upload** — file picker, accepts `.pdf` only
3. **Screenshot upload** — file picker, accepts `.png`, `.jpg`, `.jpeg`, `.webp`

Single "Analyze" button that works for whichever input is provided.

Show a loading state: "Reading the fine print..."

Results appear as `TosResultCard` components, one card per flag found. Each card has:
- Flag title (e.g. "Auto-renewal clause")
- Severity: `high`, `medium`, `low` — shown as a colored badge (red, yellow, green)
- Plain English explanation of the clause
- Exact quote from the document where possible

At the top of results, show a **Risk Summary**: a plain sentence like "This agreement has 3 high-risk financial clauses. Review before signing."

Store analysis results in Firestore under `users/{uid}/tos_analyses` with timestamp and source URL or filename.

### Backend (`routers/tos.py`)

- `POST /tos/analyze-url` — accepts `{ url: string }`, fetches page content server-side using `httpx`, extracts text from HTML using `BeautifulSoup`, passes to Gemini
- `POST /tos/analyze-file` — accepts multipart file upload (PDF or image), stores temporarily in Firebase Storage, passes to Gemini
- Both return the same structured flag list

### Gemini Service — ToS Analysis

For **URL and PDF**: use Gemini 1.5 Pro with the extracted text passed as a text prompt.
For **screenshots and images**: use Gemini 1.5 Pro's multimodal capability — pass the image bytes directly as an inline image part. This demonstrates Gemini's vision capability explicitly.

```python
# Prompt for ToS analysis
"""
You are a financial consumer protection assistant. Analyze the following Terms of Service or User Agreement document.

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
{document_content}
"""
```

---

## Feature 3: Cost Intelligence Dashboard

### Frontend (`intelligence/CostIntelligencePage.jsx`)

This page is the product's conclusion. It pulls from both Gmail scan results and ToS analyses stored in Firestore.

Sections:

**1. Subscription Map**
- Visual summary of all active subscriptions
- Total monthly spend calculated and displayed prominently
- Grouped by category
- Each subscription shows: logo/icon placeholder, service name, amount, frequency, category badge
- Flag subscriptions with no recent charge in 90+ days as "Possibly forgotten"

**2. Wasteful Spend Flags**
- Highlight duplicate categories (e.g. two streaming services, two cloud storage services)
- Flag trials ending within 7 days
- Flag subscriptions with high-risk ToS clauses already analyzed

**3. Alternatives & Savings (Gemini Search Grounded)**
- For each flagged or expensive subscription, show AI-generated alternatives
- Use Gemini with Google Search grounding for live results
- Show: alternative service name, estimated cost, key difference, source link

**4. Platform Sentiment**
- For each subscription, show a brief synthesized sentiment: "Users on Reddit and Trustpilot report cancellation is difficult. Support response times are slow."
- Powered by Gemini with Google Search grounding

### Backend (`routers/intelligence.py`)

- `GET /intelligence/summary` — pulls user's subscriptions and ToS analyses from Firestore, returns combined summary
- `POST /intelligence/alternatives` — accepts `{ service_name: string, current_amount: number, currency: string }`, calls Gemini with search grounding, returns alternatives
- `POST /intelligence/sentiment` — accepts `{ service_name: string }`, calls Gemini with search grounding, returns sentiment summary

### Gemini Service — Alternatives (with Search Grounding)

```python
# Enable Google Search grounding tool
tools = [{"google_search": {}}]

# Prompt for alternatives
"""
The user currently pays {amount} {currency} per {frequency} for {service_name}.

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

Return ONLY valid JSON. No markdown.
"""
```

```python
# Prompt for sentiment
"""
Search for recent user reviews, complaints, and feedback about {service_name} subscription service.
Focus on: cancellation experience, billing surprises, customer support quality, and overall value.

Summarize in 2-3 sentences what users are generally saying. Be specific and honest.
Mention the sources (Reddit, Trustpilot, App Store, etc.) where you found this.

Return a JSON object with:
- sentiment: "positive" | "mixed" | "negative"
- summary: string (2-3 sentences)
- sources: array of strings

Return ONLY valid JSON. No markdown.
"""
```

---

## Deployment — Google Cloud Run

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Frontend Dockerfile

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

### nginx.conf

```nginx
server {
    listen 8080;
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    location /api {
        proxy_pass http://backend:8080;
    }
}
```

### docker-compose.yml (for local development)

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8080"
    env_file:
      - ./backend/.env
  frontend:
    build: ./frontend
    ports:
      - "3000:8080"
    env_file:
      - ./frontend/.env
    depends_on:
      - backend
```

### Cloud Run Deployment Commands

Leave these as comments in a `deploy.sh` script at the root. The developer will run these after filling in project ID:

```bash
# deploy.sh
# Fill in your Google Cloud project ID before running

PROJECT_ID=your_project_id_here
REGION=us-central1

# Deploy backend
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/[add-funny-name]-backend
gcloud run deploy [add-funny-name]-backend \
  --image gcr.io/$PROJECT_ID/[add-funny-name]-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY,FEATHERLESS_API_KEY=$FEATHERLESS_API_KEY,GMAIL_CLIENT_ID=$GMAIL_CLIENT_ID,GMAIL_CLIENT_SECRET=$GMAIL_CLIENT_SECRET,FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"

# Deploy frontend
cd ../frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/[add-funny-name]-frontend
gcloud run deploy [add-funny-name]-frontend \
  --image gcr.io/$PROJECT_ID/[add-funny-name]-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
```

---

## Backend `requirements.txt`

```
fastapi
uvicorn
google-generativeai
google-auth
google-auth-oauthlib
google-api-python-client
firebase-admin
openai
httpx
beautifulsoup4
python-multipart
pypdf2
pillow
python-dotenv
pydantic
```

---

## Frontend `package.json` dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "firebase": "^10.8.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## Implementation Priority Order

Build in this exact order. Each step should be functional before moving to the next:

1. **Project scaffold** — folder structure, Dockerfiles, env placeholder files, docker-compose working locally
2. **Firebase auth** — signup, login, Google Sign-In working end to end, protected routes on frontend, token verification middleware on backend
3. **Firestore setup** — user document creation on signup, basic read/write confirmed working
4. **ToS Analyzer** — URL input first, then PDF, then image. This is the fastest to demo and requires no OAuth beyond Firebase.
5. **Gmail OAuth flow** — connect Gmail, store tokens, confirm token retrieval works
6. **Gmail Scanner** — fetch emails, Gemini extraction, Featherless categorization, store in Firestore
7. **Cost Intelligence Dashboard** — pull from Firestore, Gemini alternatives with search grounding, Gemini sentiment with search grounding
8. **Deployment to Cloud Run** — backend first, frontend second, confirm public URLs work
9. **Auth polish** — only if time allows

---

## Important Notes for Cursor

- Never store raw Gmail tokens unencrypted. Store them in Firestore but note in a comment that production would encrypt them.
- All Gemini prompts must request JSON-only responses. Always wrap Gemini response parsing in try/except and return a clear error if JSON parsing fails.
- The Featherless API is OpenAI-compatible. Use the `openai` Python SDK with `base_url="https://api.featherless.ai/v1"` and `api_key=FEATHERLESS_API_KEY`.
- For Gmail scanning, handle token expiry — use the refresh token to get a new access token if the current one is expired before making Gmail API calls.
- All backend endpoints must return consistent JSON error responses: `{ "error": true, "message": "...", "code": "..." }`
- Use `python-dotenv` to load `.env` in development. On Cloud Run, environment variables are set via the deployment command.
- Frontend API calls must use the `VITE_API_BASE_URL` env variable as the base — never hardcode localhost.
- Add a `/health` endpoint to the FastAPI backend that returns `{ "status": "ok" }` — Cloud Run uses this for health checks.
