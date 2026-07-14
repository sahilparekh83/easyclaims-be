#!/usr/bin/env bash
# Deploy EasyClaims backend to Google Cloud Run for testing.
# Prereqs: `gcloud` CLI installed and authenticated (gcloud auth login),
# and a GCP project with billing enabled.
#
# Usage:
#   PROJECT_ID=your-gcp-project REGION=asia-south1 ./deploy_cloud_run.sh
set -euo pipefail
cd "$(dirname "$0")"

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID=your-gcp-project-id}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${SERVICE_NAME:-easyclaims-backend}"

echo "==> Using project: $PROJECT_ID  region: $REGION  service: $SERVICE_NAME"
gcloud config set project "$PROJECT_ID"

echo "==> Enabling required APIs (safe to re-run)"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

echo "==> Building and deploying from source (uses the repo's Dockerfile)"
# --allow-unauthenticated is attempted but may warn if the org enforces Domain
# Restricted Sharing (blocks allUsers) — gcloud still exits 0 in that case.
# A genuine deploy failure (bad image, crash on startup, etc.) exits nonzero
# and stops the script here (set -e) rather than silently continuing.
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --env-vars-file env.yaml

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')
echo "==> Deployed at: $SERVICE_URL"

echo "==> Updating BACKEND_URL to the live Cloud Run URL"
gcloud run services update "$SERVICE_NAME" \
    --region "$REGION" \
    --update-env-vars "BACKEND_URL=$SERVICE_URL"

DEPLOYER=$(gcloud config get-value account 2>/dev/null)
echo "==> Granting $DEPLOYER invoker access (org policy blocks public/allUsers access)"
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
    --region "$REGION" \
    --member="user:$DEPLOYER" \
    --role="roles/run.invoker" || true

echo "==> Done. Test it (requires an identity token — see README.md):"
echo "    TOKEN=\$(gcloud auth print-identity-token)"
echo "    curl -H \"Authorization: Bearer \$TOKEN\" $SERVICE_URL/api/v1/health"
echo "    open $SERVICE_URL/docs (with the same header, e.g. via a browser extension, or use curl)"
