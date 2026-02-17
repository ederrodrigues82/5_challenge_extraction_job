"""
Pydantic models for the Extraction Job API.
Do not modify this file.
"""

from pydantic import BaseModel, Field


class CreateExtractionJobRequest(BaseModel):
    """Request body for POST /extraction-jobs."""

    document_id: str = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0, le=10)
    metadata: dict | None = None


class UpdateExtractionJobRequest(BaseModel):
    """Request body for PATCH /extraction-jobs/{id}."""

    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    error_message: str | None = None

#create a model that will be used to store the extraction job in the database
class ExtractionJob(BaseModel):
    id: str
    document_id: str
    status: str
    priority: int
    metadata: dict | None
    error_message: str | None
    created_at: str
    updated_at: str

class ExtractionJobResponse(ExtractionJob):
    """Response model for extraction job."""
    def __init__(self, **data: dict):
        super().__init__(**data)
