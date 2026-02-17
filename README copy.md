# Extraction Job API — Live Coding Challenge

**Level:** Senior | **Time:** ~60 minutes | **Type:** Build from scratch

## Context

Canoe's Data Services team processes documents through extraction pipelines. When a document is ingested, an extraction job is created to track the lifecycle from pending → processing → completed or failed. This challenge asks you to implement an **Extraction Job API** that manages these jobs for operational visibility and downstream integrations.

## Setup

```bash
cd 5_challenge_extraction_job
python -m venv venv
venv\Scripts\activate   # Windows
# or: source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

## Your Task

**Implement the API in `main.py` from scratch** so that all tests pass. Do not modify `test_extraction_job.py` or `models.py`.

To start the challenge, replace `main.py` with the contents of `main_starter.py` (or use `main_starter.py` as your starting point).

Run tests:

```bash
pytest test_extraction_job.py -v
```

Tests run with auth disabled (`AUTH_DISABLED=1` set in conftest.py). To test with real Auth0 auth, unset `AUTH_DISABLED` and pass a valid Bearer token in the `Authorization` header.

## Auth0 Authentication

All endpoints require a valid OAuth2 Bearer token from Auth0. Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH0_DOMAIN` | `dev-wkl17exhgoi6mj0m.us.auth0.com` | Auth0 tenant |
| `AUTH0_AUDIENCE` | `https://dev-wkl17exhgoi6mj0m.us.auth0.com/api/v2/` | API identifier |
| `AUTH0_CLIENT_SECRET` | — | Required to obtain tokens (never commit) |
| `AUTH_DISABLED` | — | Set to `1` to bypass auth (e.g. for tests) |

**Obtain a token** (client credentials flow):

```bash
curl -X POST "https://dev-wkl17exhgoi6mj0m.us.auth0.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=qyjRWxz9FxlpMAKb9FHtKVB410ghBFbu" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "audience=https://dev-wkl17exhgoi6mj0m.us.auth0.com/api/v2/"
```

Use the returned `access_token` in requests: `Authorization: Bearer <access_token>`.

## Database

The API uses SQLite with SQLAlchemy ORM to persist extraction jobs. The `extraction_job` table is created automatically on startup. Pydantic schemas convert between SQLAlchemy models and API responses.

| Variable | Default | Description |
|----------|---------|--------------|
| `DATABASE_URL` | — | PostgreSQL URL. When set, used for Lambda/RDS. |
| `DB_PATH` | `extraction_jobs.db` | SQLite path when `DATABASE_URL` is not set. Use `:memory:` for ephemeral storage. |

Tests use a temporary file for the database; the `reset_store` fixture clears it between tests.

## AWS Deployment (Lambda + RDS + Terraform)

To deploy to AWS with Lambda, API Gateway, and RDS PostgreSQL:

1. **Install Terraform** (https://terraform.io/downloads)

2. **Build the Lambda package**:
   ```bash
   # Windows
   .\scripts\build_lambda.ps1
   # Linux/Mac
   ./scripts/build_lambda.sh
   ```

3. **Configure Terraform**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars: set db_password and other values
   ```

4. **Deploy** (when ready):
   ```bash
   terraform init
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

5. **Get the API URL**: `terraform output api_url`

6. **Bootstrap**: Tables are created automatically on first Lambda request.

## API Specification

- **POST /extraction-jobs** — Create an extraction job.
  - Body: `{ "document_id": str, "priority": int (0–10, default 0), "metadata": dict | null }`
  - Returns 201 with created job including `id`, `document_id`, `status` (initially `"pending"`), `priority`, `metadata`, `error_message` (null), `created_at`, `updated_at` (ISO 8601).
  - Validation: `document_id` must be non-empty; `priority` must be 0–10 (422 if invalid).

- **GET /extraction-jobs/{id}** — Get an extraction job by ID. Returns 200 or 404.

- **PATCH /extraction-jobs/{id}** — Update an extraction job.
  - Body: `{ "status": "pending" | "processing" | "completed" | "failed", "error_message": str | null }`
  - Returns 200 or 404. Updates `updated_at` on change.

- **GET /extraction-jobs** — List extraction jobs.
  - Query params: `document_id` (optional), `status` (optional), `limit` (optional), `offset` (optional).
  - Filters by `document_id` and/or `status` when provided. Pagination via `limit` and `offset` applies to the filtered result.
  - Returns 200 with list.

## Hints

- Architecture: endpoints → `ExtractionJobService` → `ExtractionJobRepository` → SQLite. Pydantic schemas handle ORM-to-API conversion.
- Use Pydantic models from `models.py` for request validation.
- Generate `id` with `uuid4()` and timestamps with `datetime.now(timezone.utc).isoformat()`.
- Read the test file to understand exact expectations.
