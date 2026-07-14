#!/usr/bin/env bash
# Run by a project admin (e.g. developer@easyclaims.in) to grant a colleague
# everything they need to run provision_gcp.sh + deploy_cloud_run.sh and call
# the deployed API.
#
# Usage:
#   PROJECT_ID=easyclaims-26493 ./grant_colleague_access.sh colleague@example.com
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID=your-gcp-project-id}"
EMAIL="${1:?Usage: ./grant_colleague_access.sh colleague@example.com}"
SERVICE_NAME="${SERVICE_NAME:-easyclaims-backend}"
REGION="${REGION:-asia-south1}"

echo "==> Granting $EMAIL project-level roles on $PROJECT_ID"
for ROLE in \
    roles/run.admin \
    roles/cloudbuild.builds.editor \
    roles/storage.admin \
    roles/iam.serviceAccountUser \
    roles/serviceusage.serviceUsageAdmin \
    roles/cloudsql.client \
    roles/artifactregistry.writer
do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="user:$EMAIL" \
        --role="$ROLE" \
        --condition=None \
        --quiet
done

echo "==> Granting $EMAIL invoker access on the Cloud Run service (if it exists yet)"
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --member="user:$EMAIL" \
    --role="roles/run.invoker" || echo "    (service not deployed yet — re-run this after first deploy, or the colleague's own deploy will grant themselves access)"

echo "==> Done. $EMAIL can now: gcloud auth login, then run provision_gcp.sh and deploy_cloud_run.sh."
