from __future__ import annotations

import logging
import time
from datetime import timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.common.config import configure_logging, get_settings
from services.common.db import get_session_factory
from services.common.models import Case, CaseStatus, Job, JobStatus, JobType, utcnow
from services.common.schemas import RagAnswer, TriageResponse

configure_logging()
logger = logging.getLogger("services.worker.main")
settings = get_settings()


def claim_next_pending_job(db: Session) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.status == JobStatus.PENDING.value)
        .order_by(Job.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = db.execute(stmt).scalars().first()
    if job is None:
        return None

    job.status = JobStatus.CLAIMED.value
    job.claimed_at = utcnow()
    job.attempts += 1
    if job.job_type == JobType.ANSWER_QUESTION.value:
        case = db.get(Case, job.case_id)
        if case:
            case.status = CaseStatus.PROCESSING.value
    db.commit()
    db.refresh(job)
    return job


def mark_job_failed(job_id: int, error_message: str) -> None:
    session_factory = get_session_factory()
    with session_factory() as db:
        job = db.get(Job, job_id)
        if job is None:
            return

        case = db.get(Case, job.case_id)
        job.status = JobStatus.FAILED.value
        job.error = error_message[:1000]
        job.completed_at = utcnow()

        if case is not None:
            case.status = CaseStatus.FAILED.value

        db.commit()


def process_job(job_id: int) -> None:
    session_factory = get_session_factory()

    with session_factory() as db:
        job = db.get(Job, job_id)
        if job is None:
            return

        case = db.get(Case, job.case_id)
        if case is None:
            raise RuntimeError(f"Case not found for job {job_id}")

        payload = {
            "case_id": case.id,
            "title": case.title,
            "description": case.description,
        }
        is_question = job.job_type == JobType.ANSWER_QUESTION.value
        if is_question:
            payload = {"case_id": case.id, "question": case.description}

    response = httpx.post(
        f"{settings.ai_service_url}/rag/query"
        if is_question
        else f"{settings.ai_service_url}/triage",
        json=payload,
        timeout=(
            settings.rag_request_timeout_seconds + 15
            if is_question
            else settings.worker_request_timeout_seconds
        ),
        trust_env=False,
    )
    response.raise_for_status()
    result = (
        RagAnswer.model_validate(response.json())
        if is_question
        else TriageResponse.model_validate(response.json())
    )

    with session_factory() as db:
        job = db.get(Job, job_id)
        if job is None:
            return

        case = db.get(Case, job.case_id)
        if case is None:
            raise RuntimeError(f"Case not found while completing job {job_id}")

        if is_question:
            case.status = CaseStatus.ANSWERED.value
            case.answer = result.answer
            case.cite_pages = result.cite_pages
            case.sources = [source.model_dump() for source in result.sources]
            case.related_images = [image.model_dump() for image in result.related_images]
        else:
            case.status = CaseStatus.TRIAGED.value
            case.ai_label = result.label
            case.ai_summary = result.summary
            case.ai_confidence = result.confidence

        job.status = JobStatus.COMPLETED.value
        job.error = None
        job.completed_at = utcnow()
        db.commit()

    logger.info("job_completed", extra={"job_id": job_id, "question": is_question})


def recover_abandoned_jobs(db: Session) -> None:
    # A worker may have died after claiming a job. Keep its lease longer than the
    # HTTP deadline so another worker does not duplicate a live inference.
    lease = max(settings.rag_job_lease_seconds, settings.rag_request_timeout_seconds + 60)
    cutoff = utcnow() - timedelta(seconds=lease)
    jobs = (
        db.execute(
            select(Job)
            .where(Job.status == JobStatus.CLAIMED.value, Job.claimed_at < cutoff)
            .with_for_update(skip_locked=True)
        )
        .scalars()
        .all()
    )
    for job in jobs:
        case = db.get(Case, job.case_id)
        if job.attempts >= settings.rag_max_attempts:
            job.status = JobStatus.FAILED.value
            job.error = "任务处理已中断，请重新提问。"
            job.completed_at = utcnow()
            if case:
                case.status = CaseStatus.FAILED.value
        else:
            job.status = JobStatus.PENDING.value
            job.claimed_at = None
            if case:
                case.status = CaseStatus.QUEUED.value
    if jobs:
        db.commit()


def run_worker() -> None:
    session_factory = get_session_factory()
    logger.info(
        "worker_started",
        extra={
            "poll_seconds": settings.worker_poll_seconds,
            "ai_service_url": settings.ai_service_url,
        },
    )

    while True:
        job = None
        try:
            with session_factory() as db:
                recover_abandoned_jobs(db)
                job = claim_next_pending_job(db)

            if job is None:
                time.sleep(settings.worker_poll_seconds)
                continue

            logger.info("job_claimed", extra={"job_id": job.id, "case_id": job.case_id})
            process_job(job.id)

        except KeyboardInterrupt:
            logger.info("worker_stopped")
            raise

        except Exception:
            logger.exception("job_processing_failed")
            if job is not None:
                message = "问答服务暂时不可用或响应超时，请检查连接后重试。"
                mark_job_failed(job.id, message)
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_worker()
