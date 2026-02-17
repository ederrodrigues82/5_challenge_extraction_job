"""
Extraction Job API — Canoe Data Services
Implement this API from scratch so all tests pass.

Replace main.py with this file to start the challenge.
"""

from fastapi import FastAPI

app = FastAPI(title="Extraction Job API")

# In-memory store (tests will reset this). Implement the routes below.
extraction_jobs: dict[str, dict] = {}

# TODO: Implement POST /extraction-jobs
# TODO: Implement GET /extraction-jobs/{job_id}
# TODO: Implement PATCH /extraction-jobs/{job_id}
# TODO: Implement GET /extraction-jobs (with filters and pagination)
