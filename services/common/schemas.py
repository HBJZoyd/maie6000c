from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from services.common.models import CaseStatus, JobStatus, JobType


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str = "0.1.0"


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=4000)


class CaseRead(BaseModel):
    id: str
    title: str
    description: str
    status: CaseStatus
    ai_label: str | None = None
    ai_summary: str | None = None
    ai_confidence: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobRead(BaseModel):
    id: int
    case_id: str
    job_type: JobType
    status: JobStatus
    attempts: int
    error: str | None = None
    created_at: datetime
    claimed_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CaseCreateResponse(BaseModel):
    case: CaseRead
    job: JobRead


class TriageRequest(BaseModel):
    case_id: str
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=4000)


class TriageResponse(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)


class QuestionCreate(BaseModel):
    question: str = Field(min_length=3, max_length=4000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("请输入至少三个字符的问题")
        return value


class ManualSource(BaseModel):
    page: int = Field(ge=1)
    excerpt: str = Field(default="", max_length=4000)
    title: str = "Model 3 车主手册"


class ManualImage(BaseModel):
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    page: int = Field(ge=1)
    title: str = "手册插图"


class RagRequest(QuestionCreate):
    case_id: str | None = None


class RagAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=40000)
    cite_pages: list[int] = Field(default_factory=list, max_length=100)
    sources: list[ManualSource] = Field(default_factory=list, max_length=100)
    related_images: list[ManualImage] = Field(default_factory=list, max_length=30)

    @field_validator("cite_pages")
    @classmethod
    def valid_pages(cls, pages: list[int]) -> list[int]:
        if any(page < 1 for page in pages):
            raise ValueError("Citation pages must be positive")
        return sorted(set(pages))

    @field_validator("answer")
    @classmethod
    def nonempty_answer(cls, answer: str) -> str:
        if not answer.strip():
            raise ValueError("Empty answer")
        return answer.strip()


class QuestionRead(BaseModel):
    id: str
    question: str
    status: CaseStatus
    answer: str | None = None
    cite_pages: list[int] = Field(default_factory=list)
    sources: list[ManualSource] = Field(default_factory=list)
    related_images: list[ManualImage] = Field(default_factory=list)
    error: str | None = None
    job_id: int
    attempts: int
    created_at: datetime
    updated_at: datetime
