"""
Extraction Job API — Canoe Data Services
Implement this API from scratch so all tests pass.

Replace main.py with this file to start the challenge.
"""

import os
from typing import List, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, Query, status

from auth import get_auth_dependency
from database import DB_PATH
from models import (
    CreateExtractionJobRequest,
    ExtractionJobResponse,
    UpdateExtractionJobRequest,
)
from repository import ExtractionJobRepository
from service import ExtractionJobService

app = FastAPI(title="Extraction Job API")

# Service layer (tests reset via extraction_jobs.clear())
# DATABASE_URL for PostgreSQL (Lambda/RDS); DB_PATH for SQLite (local dev)
_db_url = os.environ.get("DATABASE_URL") or DB_PATH
extraction_job_repository = ExtractionJobRepository(_db_url)
extraction_job_service = ExtractionJobService(extraction_job_repository)
extraction_jobs = extraction_job_service


def get_extraction_job_service() -> ExtractionJobService:
    """Dependency that returns the extraction job service."""
    return extraction_job_service


@app.post("/extraction-jobs", response_model=ExtractionJobResponse, status_code=status.HTTP_201_CREATED)
def create_extraction_job(
    job: CreateExtractionJobRequest = Body(...),
    svc: ExtractionJobService = Depends(get_extraction_job_service),
    _auth: dict | None = Depends(get_auth_dependency()),
):
    return svc.create(job)


@app.get("/extraction-jobs/{job_id}", response_model=ExtractionJobResponse)
def get_extraction_job(
    job_id: str,
    svc: ExtractionJobService = Depends(get_extraction_job_service),
    _auth: dict | None = Depends(get_auth_dependency()),
):
    job = svc.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found")
    return job


@app.patch("/extraction-jobs/{job_id}", response_model=ExtractionJobResponse, status_code=status.HTTP_200_OK)
def update_extraction_job(
    job_id: str,
    update: UpdateExtractionJobRequest = Body(...),
    svc: ExtractionJobService = Depends(get_extraction_job_service),
    _auth: dict | None = Depends(get_auth_dependency()),
):
    job = svc.update(job_id, update)
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found")
    return job


@app.get(
    "/extraction-jobs",
    response_model=List[ExtractionJobResponse],
    status_code=200,
)
def list_extraction_jobs(
    document_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: Optional[int] = Query(None, ge=0),
    offset: Optional[int] = Query(None, ge=0),
    svc: ExtractionJobService = Depends(get_extraction_job_service),
    _auth: dict | None = Depends(get_auth_dependency()),
):
    return svc.list(
        document_id=document_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
