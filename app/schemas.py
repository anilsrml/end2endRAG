import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    media_type: str
    status: str
    chunk_count: int = 0
    created_at: datetime


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)


class SourceResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    page: int | None = None
    heading: str | None = None
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    model: str
    reranker_used: bool
    trace_id: str


class HealthResponse(BaseModel):
    status: str

