#!/usr/bin/env bash
# One-time (idempotent) GCP project setup for the EasyClaims test backend.
# Creates/verifies: enabled APIs, the Cloud Storage bucket for policy documents,
# and IAM so Cloud Run can read/write that bucket.
#
# Requires: gcloud CLI, authenticated (gcloud auth login) with an account that
# has Editor/Owner (or the specific roles below) on the target project.
#
# Usage:
#   PROJECT_ID=easyclaims-26493 REGION=asia-south1 ./provision_gcp.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID=your-gcp-project-id}"
REGION="${REGION:-asia-south1}"
BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-policies}"

echo "==> Project: $PROJECT_ID  Region: $REGION  Bucket: $BUCKET_NAME"
gcloud config set project "$PROJECT_ID"

echo "==> Enabling required APIs (safe to re-run)"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    iam.googleapis.com

echo "==> Checking Cloud SQL instance"
if gcloud sql instances list --format="value(name)" | grep -q .; then
    gcloud sql instances list
else
    echo "    No Cloud SQL instance found in this project."
    echo "    The backend expects Postgres already reachable via POSTGRES_SERVER in env.yaml."
    echo "    If you need a fresh instance, create one manually (this script won't, since"
    echo "    it's a billed, several-minutes operation) e.g.:"
    echo "      gcloud sql instances create easyclaims-test --database-version=POSTGRES_16 \\"
    echo "        --tier=db-f1-micro --region=$REGION --root-password=<choose-one>"
fi

echo "==> Creating GCS bucket for policy document storage (if missing)"
if gcloud storage buckets describe "gs://$BUCKET_NAME" >/dev/null 2>&1; then
    echo "    Bucket gs://$BUCKET_NAME already exists"
else
    gcloud storage buckets create "gs://$BUCKET_NAME" --location="$REGION"
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "==> Granting Cloud Run's runtime service account ($RUNTIME_SA) access to the bucket"
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" \
    --member="serviceAccount:$RUNTIME_SA" \
    --role="roles/storage.objectAdmin"

echo "==> Done. Set these in env.yaml before deploying:"
echo "    STORAGE_BACKEND: 'gcs'"
echo "    STORAGE_BUCKET: '$BUCKET_NAME'"
echo "    GCS_PROJECT: '$PROJECT_ID'"
