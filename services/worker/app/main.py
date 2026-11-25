from __future__ import annotations

import asyncio
import logging
import random
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import timedelta

import httpx
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from services.common.config import configure_logging, get_settings
from services.common.db import get_session_factory
from services.common.models import Case, CaseStatus, Job, JobAttempt, JobStatus, JobType, utcnow
from services.common.schemas import RagAnswer, TriageResponse

configure_logging()
logger = logging.getLogger("services.worker.main")
settings = get_settings()


def claim_next_pending_job(db: Session) -> Job | None:
    job = db.execute(
        select(Job).where(
            Job.status == JobStatus.PENDING.value,
            or_(Job.next_run_at.is_(None), Job.next_run_at <= utcnow()),
        ).order_by(Job.created_at, Job.id).limit(1).with_for_update(skip_locked=True)
    ).scalars().first()
    if job is None:
        return None
    token, now = str(uuid.uuid4()), utcnow()
    # CAS also makes a raced SQLite claimant harmless; PostgreSQL uses row locks.
    claimed = db.execute(
        update(Job).where(Job.id == job.id, Job.status == JobStatus.PENDING.value).values(
            status=JobStatus.CLAIMED.value, claimed_at=now, heartbeat_at=now,
            claim_token=token, attempts=Job.attempts + 1, generation=Job.generation + 1,
            error=None, next_run_at=None, completed_at=None,
        ).execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:
        db.rollback()
        return None
    db.refresh(job)
    case = db.get(Case, job.case_id)
    if case and job.job_type == JobType.ANSWER_QUESTION.value:
        case.status = CaseStatus.PROCESSING.value
    db.add(JobAttempt(id=token, job_id=job.id, generation=job.generation, started_at=now))
    db.commit()
    return job


def heartbeat(job_id: int, token: str) -> bool:
    if not token:
        return False
    with get_session_factory()() as db:
        result = db.execute(
            update(Job).where(
                Job.id == job_id, Job.claim_token == token, Job.status == JobStatus.CLAIMED.value,
            ).values(heartbeat_at=utcnow())
        )
        db.commit()
        return result.rowcount == 1


@contextmanager
def keep_lease(job_id: int, token: str):
    stopped = threading.Event()

    def renew():
        while not stopped.wait(max(0.1, settings.worker_heartbeat_seconds)):
            try:
                if not heartbeat(job_id, token):
                    return
            except Exception:
                logger.exception("heartbeat_failed", extra={"job_id": job_id, "attempt_id": token})

    thread = threading.Thread(target=renew, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stopped.set()
        thread.join(timeout=2)


def owned_job(db: Session, job_id: int, token: str) -> Job | None:
    if not token:
        return None
    return db.execute(
        select(Job).where(
            Job.id == job_id, Job.claim_token == token, Job.status == JobStatus.CLAIMED.value,
        ).with_for_update()
    ).scalar_one_or_none()


def mark_job_failed(
    job_id: int, error_message: str, token: str, *,
    error_code: str = "internal_error", retryable: bool = False, retry_after: float = 0,
) -> bool:
    with get_session_factory()() as db:
        job = owned_job(db, job_id, token)
        if job is None:
            return False
        now = utcnow()
        retry = retryable and job.attempts < settings.rag_max_attempts
        attempt = db.get(JobAttempt, token)
        if attempt:
            attempt.status = "retry_scheduled" if retry else "failed"
            attempt.finished_at, attempt.error_code = now, error_code
            attempt.error = error_message[:1000]
        job.error = error_message[:1000]
        job.claim_token, job.heartbeat_at = None, None
        if retry:
            cap = max(0, settings.rag_retry_max_seconds)
            backoff = settings.rag_retry_base_seconds * (2 ** min(job.attempts - 1, 10))
            delay = min(cap, max(retry_after, backoff + random.uniform(0, max(0, backoff / 4))))
            job.status = JobStatus.PENDING.value
            job.next_run_at, job.completed_at = now + timedelta(seconds=delay), None
        else:
            job.status, job.completed_at = JobStatus.FAILED.value, now
        case = db.get(Case, job.case_id)
        if case:
            case.status = CaseStatus.QUEUED.value if retry else CaseStatus.FAILED.value
        db.commit()
    logger.info("job_retry_scheduled" if retry else "job_failed", extra={
        "job_id": job_id, "attempt_id": token, "error_code": error_code,
    })
    return True


async def call_ai(url: str, payload: dict, budget: float) -> httpx.Response:
    # A scalar HTTPX timeout limits inactivity, not total wall time.
    async with asyncio.timeout(budget):
        async with httpx.AsyncClient(trust_env=False, timeout=min(budget, 180)) as client:
            return await client.post(url, json=payload)


def process_job(job_id: int, token: str) -> bool:
    factory = get_session_factory()
    with factory() as db:
        job = owned_job(db, job_id, token)
        if job is None:
            return False
        case = db.get(Case, job.case_id)
        if case is None:
            raise RuntimeError("Missing question")
        is_question = job.job_type == JobType.ANSWER_QUESTION.value
        payload = {"case_id": case.id, "question": case.description} if is_question else {
            "case_id": case.id, "title": case.title, "description": case.description,
        }
    budget = (settings.rag_request_timeout_seconds + 15
              if is_question else settings.worker_request_timeout_seconds)
    route = "/rag/query" if is_question else "/triage"
    with keep_lease(job_id, token):
        response = asyncio.run(call_ai(f"{settings.ai_service_url}{route}", payload, budget))
        response.raise_for_status()
        result = (RagAnswer.model_validate(response.json()) if is_question
                  else TriageResponse.model_validate(response.json()))

    with factory() as db:
        job = owned_job(db, job_id, token)
        if job is None:
            logger.warning("stale_result_discarded", extra={"job_id": job_id, "attempt_id": token})
            return False
        case = db.get(Case, job.case_id)
        if case is None:
            raise RuntimeError("Missing question")
        if is_question:
            case.status = CaseStatus.ANSWERED.value
            case.answer = result.answer
            case.cite_pages = result.cite_pages
            case.sources = [s.model_dump() for s in result.sources]
            case.related_images = [i.model_dump() for i in result.related_images]
            case.answer_payload = result.model_dump()
        else:
            case.status = CaseStatus.TRIAGED.value
            case.ai_label, case.ai_summary = result.label, result.summary
            case.ai_confidence = result.confidence
        now = utcnow()
        job.status, job.error = JobStatus.COMPLETED.value, None
        job.completed_at, job.claim_token, job.heartbeat_at = now, None, None
        attempt = db.get(JobAttempt, token)
        if attempt:
            attempt.status, attempt.finished_at = "completed", now
        db.commit()
    logger.info("job_completed", extra={"job_id": job_id, "attempt_id": token})
    return True


def recover_abandoned_jobs(db: Session) -> int:
    lease = max(settings.rag_job_lease_seconds, settings.worker_heartbeat_seconds * 3)
    cutoff = utcnow() - timedelta(seconds=lease)
    jobs = db.execute(
        select(Job).where(
            Job.status == JobStatus.CLAIMED.value,
            func.coalesce(Job.heartbeat_at, Job.claimed_at) < cutoff,
        ).with_for_update(skip_locked=True)
    ).scalars().all()
    for job in jobs:
        token = job.claim_token
        attempt = db.get(JobAttempt, token) if token else None
        if attempt:
            attempt.status, attempt.finished_at = "expired", utcnow()
            attempt.error_code, attempt.error = "lease_expired", "Worker lease expired"
        retry = job.attempts < settings.rag_max_attempts
        job.status = JobStatus.PENDING.value if retry else JobStatus.FAILED.value
        job.error = "任务执行中断，等待自动恢复。" if retry else "任务处理已中断，请重试。"
        job.claim_token, job.heartbeat_at, job.claimed_at = None, None, None
        job.next_run_at = utcnow() if retry else None
        job.completed_at = None if retry else utcnow()
        case = db.get(Case, job.case_id)
        if case:
            case.status = CaseStatus.QUEUED.value if retry else CaseStatus.FAILED.value
    if jobs:
        db.commit()
    return len(jobs)


def execute_claimed_job(job_id: int, token: str) -> bool:
    try:
        return process_job(job_id, token)
    except (httpx.TimeoutException, TimeoutError):
        code, retryable, retry_after = "timeout", True, 0
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        code = "busy" if status == 429 else f"upstream_{status}"
        retryable = (status in {429, 502, 503, 504}
                     and exc.response.headers.get("X-RAG-Retryable") != "false")
        try:
            retry_after = max(0, float(exc.response.headers.get("Retry-After", "0")))
        except ValueError:
            retry_after = 0
    except httpx.RequestError:
        code, retryable, retry_after = "connection_error", True, 0
    except Exception:
        logger.exception("job_processing_failed", extra={"job_id": job_id, "attempt_id": token})
        code, retryable, retry_after = "invalid_result_or_internal_error", False, 0
    mark_job_failed(
        job_id, "问答服务暂时无法完成请求，请稍后重试。", token,
        error_code=code, retryable=retryable, retry_after=retry_after,
    )
    return False


def run_worker():
    logger.info("worker_started")
    while True:
        try:
            with get_session_factory()() as db:
                recover_abandoned_jobs(db)
                job = claim_next_pending_job(db)
            if job is None:
                time.sleep(settings.worker_poll_seconds)
                continue
            logger.info("job_claimed", extra={
                "job_id": job.id, "case_id": job.case_id, "attempt_id": job.claim_token,
            })
            execute_claimed_job(job.id, job.claim_token)
        except KeyboardInterrupt:
            raise
        except Exception:
            logger.exception("worker_loop_failed")
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run_worker()
