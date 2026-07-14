# EasyClaims Backend — Test Deploy Package

Self-contained bundle to deploy this backend to Google Cloud Run for testing.
Includes the app source, GCP provisioning script, deploy script, and a
pre-filled test environment file (`env.yaml`).

**GCP Project:** `easyclaims-26493` (shared test project — everyone deploys to
the same Cloud Run service; each redeploy just creates a new revision).

## Security note

`env.yaml` contains real test credentials (DB password, API keys). It's
already excluded from git (`.gitignore`), but since you're sharing this zip
directly, treat it as a secret file — don't upload the zip anywhere public.

## One-time setup (per person)

1. **Install the Google Cloud SDK**
   - Windows: `winget install Google.CloudSDK`
   - Mac: `brew install --cask google-cloud-sdk`
   - Or download from https://cloud.google.com/sdk/docs/install

2. **Log in**
   ```bash
   gcloud auth login
   ```
   Use the Google account an admin has granted access to `easyclaims-26493`
   (ask developer@easyclaims.in if you get a permissions error — they can run
   `grant_colleague_access.sh` to add you).

3. **Unzip this package and open a terminal in the extracted folder.**

## Deploy

```bash
# 1. One-time infra setup (creates the GCS bucket, enables APIs) — safe to re-run
PROJECT_ID=easyclaims-26493 REGION=asia-south1 ./provision_gcp.sh

# 2. Build + deploy to Cloud Run
PROJECT_ID=easyclaims-26493 REGION=asia-south1 ./deploy_cloud_run.sh
```

The deploy script builds the container from the included `Dockerfile` via
Cloud Build, deploys to Cloud Run, and grants **your own account** invoker
access (the org blocks public/anonymous access, so every tester needs to be
explicitly granted — the script does this automatically for whoever is
logged in via `gcloud auth login`).

At the end it prints the service URL, e.g.:
```
https://easyclaims-backend-733466900359.asia-south1.run.app
```

## Testing the deployed API

The service is public — no auth token needed:

```bash
curl https://<service-url>/api/v1/health
```

Swagger UI is at `https://<service-url>/docs`.

(Earlier deploys hit an org policy blocking public/`allUsers` access to
Cloud Run; that restriction is no longer in effect on this project. If it
ever comes back, `deploy_cloud_run.sh` still auto-grants the deploying
account invoker access as a fallback.)

## Local development instead of Cloud Run

```bash
./setup_and_run.sh
```
Creates a local venv, installs dependencies, writes `.env` (same test
credentials), runs migrations, and starts the server on `localhost:8000`
with `--reload`.

## What's provisioned

- **Database:** existing Cloud SQL Postgres instance
  `easyclaims-26493-2-instance` (`34.93.116.99`) — shared, already has
  the schema migrated and seed data loaded. No need to recreate it.
- **Storage:** GCS bucket `easyclaims-26493-policies` for uploaded policy
  documents (Cloud Run's local disk doesn't persist across
  requests/revisions, so this is required — `provision_gcp.sh` creates it
  and grants Cloud Run's service account access).
- **Backend:** Cloud Run service `easyclaims-backend` in `asia-south1`.

## Granting a new colleague access (admin only)

```bash
PROJECT_ID=easyclaims-26493 ./grant_colleague_access.sh newperson@example.com
```

## Files in this package

| File | Purpose |
|------|---------|
| `provision_gcp.sh` | One-time GCP infra setup (APIs, storage bucket, IAM) |
| `deploy_cloud_run.sh` | Build + deploy the backend to Cloud Run |
| `grant_colleague_access.sh` | Admin script to onboard a new colleague |
| `setup_and_run.sh` | Local dev run (venv + uvicorn --reload) |
| `env.yaml` | Test environment variables used by Cloud Run deploy |
| `Dockerfile` | Container build definition (used by Cloud Build) |
| `app/`, `main.py`, etc. | Application source |
