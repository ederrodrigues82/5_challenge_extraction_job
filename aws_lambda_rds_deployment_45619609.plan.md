---
name: AWS Lambda RDS Deployment
overview: Deploy the Extraction Job API to AWS using Lambda (Mangum), API Gateway, RDS PostgreSQL, and Terraform for infrastructure-as-code. The plan covers application changes (PostgreSQL support, Mangum handler), Terraform modules, and deployment workflow.
todos: []
isProject: false
---

# AWS Lambda + RDS PostgreSQL Deployment Plan

## Architecture Overview

```mermaid
flowchart TB
    subgraph client [Client]
        User[User / API Client]
    end

    subgraph aws [AWS Cloud]
        subgraph public [Public]
            APIGW[API Gateway HTTP API]
        end

        subgraph vpc [VPC]
            subgraph private [Private Subnets]
                Lambda[Lambda Function]
            end
            subgraph db_subnet [DB Subnets]
                RDS[(RDS PostgreSQL)]
            end
        end
    end

    User -->|HTTPS| APIGW
    APIGW -->|Invoke| Lambda
    Lambda -->|psycopg2| RDS
```



---

## 1. Application Changes

### 1.1 Add Mangum and PostgreSQL Driver

Update [requirements.txt](5_challenge_extraction_job/requirements.txt):

- Add `mangum>=0.17.0` (ASGI-to-Lambda adapter)
- Add `psycopg2-binary>=2.9.0` (PostgreSQL driver for SQLAlchemy)

### 1.2 Create Lambda Handler Entry Point

Create new file `lambda_handler.py` in the project root:

```python
from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off")
```

- `lifespan="off"` avoids FastAPI lifespan events (simpler for Lambda)
- Mangum converts API Gateway events to ASGI and returns responses

### 1.3 Refactor Database Layer for PostgreSQL

Modify [database.py](5_challenge_extraction_job/database.py):

- **Replace `DB_PATH` with `DATABASE_URL**`: Use `os.environ.get("DATABASE_URL")`; if absent, fall back to SQLite for local dev (`sqlite:///extraction_jobs.db`).
- **PostgreSQL URL format**: `postgresql://user:pass@host:5432/dbname`
- **Engine creation**: When `DATABASE_URL` is set, use it directly; omit `check_same_thread` (SQLite-only).
- **Connection pooling**: For Lambda, use `pool_pre_ping=True` and `pool_size=2`, `max_overflow=0` to avoid connection exhaustion.

Modify [repository.py](5_challenge_extraction_job/repository.py):

- **Constructor**: Change `ExtractionJobRepository(db_path: str)` to accept `db_url: str | None` (or keep `db_path` as alias for backward compatibility and map `DATABASE_URL` internally).
- **init_db**: Pass the URL/path to `database.init_db()`.

Modify [main.py](5_challenge_extraction_job/main.py):

- Initialize `ExtractionJobRepository` with `os.environ.get("DATABASE_URL", DB_PATH)` so it uses PostgreSQL in Lambda and SQLite locally.

### 1.4 Lambda-Friendly Initialization

- **Lazy init**: Ensure `init_db()` runs on first request (or at handler cold start) rather than at import time, to avoid connection errors if env vars are not yet available.
- **Module-level singletons**: The existing `_engines` and `_session_factories` caches are fine; Lambda reuses execution contexts, so connections will be reused across invocations in the same instance.

---

## 2. Terraform Infrastructure

### 2.1 Directory Structure

```
5_challenge_extraction_job/
├── terraform/
│   ├── main.tf           # Provider, backend (optional)
│   ├── variables.tf      # Input variables
│   ├── outputs.tf        # API URL, RDS endpoint, etc.
│   ├── vpc.tf            # VPC, subnets, security groups
│   ├── rds.tf            # RDS PostgreSQL instance
│   ├── lambda.tf         # Lambda function, IAM role
│   ├── api_gateway.tf    # HTTP API + integration
│   └── terraform.tfvars  # Variable values (gitignored for secrets)
```

### 2.2 Core Terraform Resources


| Resource                    | Purpose                                                           |
| --------------------------- | ----------------------------------------------------------------- |
| **VPC**                     | Default VPC or custom with public/private subnets                 |
| **Security Group (RDS)**    | Inbound 5432 from Lambda SG only                                  |
| **Security Group (Lambda)** | Outbound to RDS SG; no inbound needed                             |
| **RDS PostgreSQL**          | `db.t3.micro` or `db.t4g.micro`, single-AZ for cost               |
| **Lambda**                  | Python 3.11+, 512MB RAM, 30s timeout; in VPC private subnet       |
| **API Gateway HTTP API**    | Routes `ANY /{proxy+}` and `ANY /` to Lambda                      |
| **IAM**                     | Lambda execution role; RDS access via VPC (no special IAM for DB) |


### 2.3 RDS Configuration

- **Engine**: `postgres` (PostgreSQL 15 or 16)
- **Instance**: `db.t3.micro` (free tier eligible) or `db.t4g.micro`
- **Storage**: 20 GB gp3, auto-scaling disabled for simplicity
- **Credentials**: Store in Terraform variables (or AWS Secrets Manager); pass to Lambda via env
- **Subnet**: Private DB subnet; Lambda in same VPC to connect

### 2.4 Lambda Configuration

- **Runtime**: `python3.11`
- **Handler**: `lambda_handler.handler`
- **Package**: Zip deployment (include app code + dependencies from `pip install -r requirements.txt -t .`)
- **Environment variables**:
  - `DATABASE_URL` = `postgresql://user:pass@rds-endpoint:5432/extraction_jobs`
  - `AUTH0_DOMAIN`, `AUTH0_AUDIENCE` (Auth0 config)
  - `AUTH_DISABLED` = `0` (or `1` for testing)
- **VPC**: Attach to private subnets; ensure NAT Gateway or VPC endpoints for outbound (Auth0 JWKS, etc.)

### 2.5 API Gateway

- **Type**: HTTP API (cheaper than REST API)
- **Integration**: Lambda proxy integration
- **CORS**: Enable if frontend will call the API
- **Output**: Invoke URL (e.g. `https://xxx.execute-api.region.amazonaws.com`)

### 2.6 Database Bootstrap

- **Option A**: Run `Base.metadata.create_all(engine)` on first Lambda cold start (already in `init_db`).
- **Option B**: One-time script (e.g. `scripts/init_db.py`) run locally with `DATABASE_URL` pointing at RDS after deploy, or from a temporary EC2/bastion.

---

## 3. Deployment Workflow

### 3.1 Build Lambda Package

```bash
# Create deployment package
pip install -r requirements.txt -t package/
cp -r *.py package/   # or use a build script
cd package && zip -r ../lambda.zip .
```

- Exclude `venv/`, `__pycache__/`, `tests/`, `.env`, `*.db`
- Include: `main.py`, `auth.py`, `database.py`, `db_models.py`, `models.py`, `repository.py`, `schemas.py`, `service.py`, `lambda_handler.py`

### 3.2 Terraform Apply

```bash
cd terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### 3.3 Post-Deploy

1. Create RDS database and user (Terraform can provision DB + user via `postgres` default).
2. Run migrations / `create_all` (via init script or first Lambda request).
3. Test API: `curl https://<api-url>/extraction-jobs` with `Authorization: Bearer <token>`.

---

## 4. Security and Secrets

- **RDS password**: Use `terraform.tfvars` (gitignored) or AWS Secrets Manager; reference in Lambda env.
- **Auth0 client secret**: Not needed for API (JWT validation only); `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` are public.
- **VPC**: Lambda in private subnet needs NAT Gateway for outbound (Auth0 JWKS, PyPI if needed). For cost savings, consider VPC endpoints for S3/DynamoDB if used, or use public subnet for Lambda (less secure).

---

## 5. Files to Create or Modify


| Action | File                                                             |
| ------ | ---------------------------------------------------------------- |
| Create | `lambda_handler.py`                                              |
| Modify | `requirements.txt` (add mangum, psycopg2-binary)                 |
| Modify | `database.py` (DATABASE_URL, PostgreSQL support)                 |
| Modify | `repository.py` (accept db_url)                                  |
| Modify | `main.py` (pass DATABASE_URL to repository)                      |
| Create | `terraform/main.tf`, `variables.tf`, `outputs.tf`                |
| Create | `terraform/vpc.tf`, `rds.tf`, `lambda.tf`, `api_gateway.tf`      |
| Create | `scripts/build_lambda.sh` or `Makefile` for packaging            |
| Update | `.gitignore` (add `terraform.tfvars`, `*.tfstate`, `lambda.zip`) |


---

## 6. Cost Considerations

- **Lambda**: Free tier covers 1M requests/month
- **API Gateway HTTP API**: ~$1 per million requests
- **RDS db.t3.micro**: ~$15/month (single-AZ)
- **NAT Gateway**: ~$32/month (consider VPC endpoints or public Lambda for dev)

---

## 7. Testing Strategy

- **Local**: Keep SQLite via `DB_PATH` or unset `DATABASE_URL`; run `uvicorn main:app`
- **Lambda**: Use `mangum` locally with `python -c "from lambda_handler import handler; ..."` or deploy and hit API Gateway
- **Integration**: Run `pytest` against local SQLite; optional integration tests against deployed API with `AUTH_DISABLED=1` for CI

