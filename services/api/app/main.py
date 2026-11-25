from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from services.common.config import configure_logging, get_settings
from services.common.db import get_db
from services.common.models import Case, CaseStatus, Job, JobAttempt, JobStatus, JobType
from services.common.rag_client import RagUnavailable, fetch_manual_asset
from services.common.schemas import (
    CaseCreate,
    CaseCreateResponse,
    CaseRead,
    HealthResponse,
    JobRead,
    QuestionCreate,
    QuestionRead,
)

configure_logging()
logger = logging.getLogger("services.api.main")

app = FastAPI(title="Model 3 Manual Q&A", version="0.2.0")
WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")

HTTP_REQUESTS = Counter(
    "api_http_requests_total",
    "Total API HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_LATENCY = Histogram(
    "api_http_request_duration_seconds",
    "API request duration in seconds",
    ["method", "path"],
)
CASES_CREATED = Counter("api_cases_created_total", "Total cases created")


def create_case_with_job(db: Session, payload: CaseCreate) -> tuple[Case, Job]:
    case = Case(
        title=payload.title.strip(),
        description=payload.description.strip(),
        status=CaseStatus.QUEUED.value,
    )
    db.add(case)
    db.flush()

    job = Job(
        case_id=case.id,
        job_type=JobType.TRIAGE_CASE.value,
        status=JobStatus.PENDING.value,
    )
    db.add(job)
    db.commit()
    db.refresh(case)
    db.refresh(job)
    return case, job


def list_cases(db: Session, limit: int) -> list[Case]:
    stmt = select(Case).order_by(Case.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def get_case(db: Session, case_id: str) -> Case | None:
    return db.get(Case, case_id)


def get_job(db: Session, job_id: int) -> Job | None:
    return db.get(Job, job_id)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    start = perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration = perf_counter() - start
        path = request.url.path
        status = str(response.status_code) if response is not None else "500"
        HTTP_REQUESTS.labels(request.method, path, status).inc()
        HTTP_REQUEST_LATENCY.labels(request.method, path).observe(duration)
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": path,
                "status_code": status,
                "duration_seconds": round(duration, 4),
            },
        )


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(service="api", status="ok")


@app.get("/health/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return HealthResponse(service="api", status="ok")


@app.get("/health/ready", response_model=HealthResponse)
def health_ready(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return HealthResponse(service="api", status="ok")


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/cases", response_model=CaseCreateResponse, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseCreateResponse:
    case, job = create_case_with_job(db, payload)
    CASES_CREATED.inc()
    logger.info("case_created", extra={"case_id": case.id, "job_id": job.id})
    return CaseCreateResponse(
        case=CaseRead.model_validate(case),
        job=JobRead.model_validate(job),
    )


@app.get("/cases", response_model=list[CaseRead])
def read_cases(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CaseRead]:
    return [CaseRead.model_validate(case) for case in list_cases(db, limit)]


@app.get("/cases/{case_id}", response_model=CaseRead)
def read_case(case_id: str, db: Session = Depends(get_db)) -> CaseRead:
    case = get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseRead.model_validate(case)


@app.get("/jobs/{job_id}", response_model=JobRead)
def read_job(job_id: int, db: Session = Depends(get_db)) -> JobRead:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job)


@app.get("/app", include_in_schema=False)
def manual_app() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})


def question_record(db: Session, case: Case) -> QuestionRead:
    job = (
        db.execute(
            select(Job).where(Job.case_id == case.id, Job.job_type == JobType.ANSWER_QUESTION.value)
        )
        .scalars()
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionRead(
        id=case.id,
        question=case.description,
        status=case.status,
        answer=case.answer,
        cite_pages=case.cite_pages or [],
        sources=case.sources or [],
        related_images=case.related_images or [],
        answer_type=(case.answer_payload or {}).get("answer_type"),
        manual=(case.answer_payload or {}).get("manual"),
        provenance=(case.answer_payload or {}).get("provenance"),
        steps=(case.answer_payload or {}).get("steps", []),
        next_run_at=job.next_run_at,
        error=job.error,
        job_id=job.id,
        attempts=job.attempts,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@app.post("/questions", response_model=QuestionRead, status_code=202)
def create_question(
    payload: QuestionCreate, db: Session = Depends(get_db),
    idempotency_key: str | None = Header(
        default=None, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"
    ),
) -> QuestionRead:
    def existing():
        record = db.execute(select(Case).where(Case.idempotency_key == idempotency_key)).scalar()
        if record and record.description != payload.question:
            raise HTTPException(status_code=409, detail="Idempotency key already used")
        return record

    if idempotency_key and (record := existing()):
        return question_record(db, record)
    case = Case(
        title=payload.question[:200], description=payload.question, status=CaseStatus.QUEUED.value,
        idempotency_key=idempotency_key,
    )
    db.add(case)
    try:
        db.flush()
        db.add(Job(case_id=case.id, job_type=JobType.ANSWER_QUESTION.value, status="pending"))
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key and (record := existing()):
            return question_record(db, record)
        raise
    db.refresh(case)
    return question_record(db, case)


@app.get("/questions", response_model=list[QuestionRead])
def read_questions(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[QuestionRead]:
    cases = (
        db.execute(
            select(Case)
            .join(Job)
            .where(Job.job_type == JobType.ANSWER_QUESTION.value)
            .order_by(Case.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [question_record(db, case) for case in cases]


@app.get("/questions/{question_id}", response_model=QuestionRead)
def read_question(question_id: str, db: Session = Depends(get_db)) -> QuestionRead:
    case = db.get(Case, question_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question_record(db, case)


@app.post("/questions/{question_id}/retry", response_model=QuestionRead, status_code=202)
def retry_question(question_id: str, db: Session = Depends(get_db)) -> QuestionRead:
    # Lock order is always Job then Case, matching worker completion/recovery.
    job = db.execute(select(Job).where(
        Job.case_id == question_id, Job.job_type == JobType.ANSWER_QUESTION.value,
    ).with_for_update()).scalar_one_or_none()
    case = db.get(Case, question_id) if job else None
    if case is None or job is None:
        raise HTTPException(status_code=404, detail="Question not found")
    question_record(db, case)
    if case.status != CaseStatus.FAILED.value:
        raise HTTPException(status_code=409, detail="Only failed questions can be retried")
    job.status = JobStatus.PENDING.value
    job.error = None
    job.claimed_at = None
    job.completed_at = None
    job.attempts = 0
    job.claim_token, job.heartbeat_at, job.next_run_at = None, None, None
    case.status = CaseStatus.QUEUED.value
    db.commit()
    db.refresh(case)
    return question_record(db, case)


@app.get("/questions/{question_id}/attempts")
def question_attempts(question_id: str, db: Session = Depends(get_db)) -> list[dict]:
    case = db.get(Case, question_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Question not found")
    question_record(db, case)
    rows = db.execute(select(JobAttempt).join(Job).where(
        Job.case_id == question_id,
    ).order_by(JobAttempt.generation)).scalars().all()
    return [{"attempt_id": a.id, "generation": a.generation, "status": a.status,
             "started_at": a.started_at, "finished_at": a.finished_at,
             "error_code": a.error_code, "error": a.error} for a in rows]


@app.get("/system/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    try:
        response = httpx.get(
            f"{get_settings().ai_service_url}/rag/status", timeout=5.0, trust_env=False
        )
        response.raise_for_status()
        backend = response.json()
        ready = backend.get("ready") is True
    except (httpx.HTTPError, ValueError):
        ready = False
    return {"api": "ready", "database": "ready", "rag": "ready" if ready else "unavailable",
            "mode": backend.get("mode", "unknown") if ready else "unknown"}


@app.get("/manual.pdf", include_in_schema=False)
def manual_pdf(sha256: str | None = Query(default=None, pattern=r"^[a-f0-9]{64}$")) -> Response:
    try:
        asset = fetch_manual_asset("/rag/manual")
    except RagUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if sha256 and asset.headers.get("X-Document-SHA256") != sha256:
        raise HTTPException(status_code=409,
                            detail="The saved answer uses a different manual version")
    return Response(
        asset.content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="Model3-Manual.pdf"'},
    )


@app.get("/manual-images/{image_id}", include_in_schema=False)
def manual_image(image_id: str) -> Response:
    import re

    if not re.fullmatch(r"[a-f0-9]{32}", image_id):
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        asset = fetch_manual_asset(f"/rag/images/{image_id}")
    except RagUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    media_type = asset.headers.get("content-type", "application/octet-stream")
    if media_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=502, detail="Invalid image type")
    return Response(
        asset.content, media_type=media_type, headers={"X-Content-Type-Options": "nosniff"}
    )
