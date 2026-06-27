#!/bin/bash
# deploy.sh
# Fill in your Google Cloud project ID before running

PROJECT_ID=your_project_id_here
REGION=us-central1

# Deploy backend
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/receipts-backend
gcloud run deploy receipts-backend \
  --image gcr.io/$PROJECT_ID/receipts-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY,FEATHERLESS_API_KEY=$FEATHERLESS_API_KEY,GMAIL_CLIENT_ID=$GMAIL_CLIENT_ID,GMAIL_CLIENT_SECRET=$GMAIL_CLIENT_SECRET,FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID,FIREBASE_PRIVATE_KEY=$FIREBASE_PRIVATE_KEY,FIREBASE_CLIENT_EMAIL=$FIREBASE_CLIENT_EMAIL,FIREBASE_STORAGE_BUCKET=$FIREBASE_STORAGE_BUCKET,FRONTEND_URL=$FRONTEND_URL,GMAIL_REDIRECT_URI=$GMAIL_REDIRECT_URI"

# Deploy frontend
# Note: VITE_* vars must be passed as Docker build args at build time.
# Example with Cloud Build substitutions:
#   gcloud builds submit --config=cloudbuild-frontend.yaml
cd ../frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/receipts-frontend
gcloud run deploy receipts-frontend \
  --image gcr.io/$PROJECT_ID/receipts-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
