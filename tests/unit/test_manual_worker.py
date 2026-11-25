from datetime import timedelta

import httpx
import pytest
from sqlalchemy import select

from services.common.db import make_session_factory
from services.common.models import Case, Job, JobAttempt, utcnow
from services.worker.app import main as worker
from tests.rag_fixtures import make_answer


@pytest.fixture()
def question_job(db_session, monkeypatch):
    factory = make_session_factory(db_session.bind)
    monkeypatch.setattr(worker, "get_session_factory", lambda: factory)
    case = Case(title="Model 3 哨兵模式", description="哨兵模式怎么用？", status="queued")
    db_session.add(case)
    db_session.flush()
    job = Job(case_id=case.id, job_type="answer_question", status="pending")
    db_session.add(job)
    db_session.commit()
    return case.id, job.id, factory


def claim(factory):
    with factory() as db:
        job = worker.claim_next_pending_job(db)
        return job.id, job.claim_token


def install_reply(monkeypatch, status=200, body=None, headers=None):
    async def reply(url, payload, budget):
        return httpx.Response(status, request=httpx.Request("POST", url),
                              json=body if body is not None else make_answer(), headers=headers)
    monkeypatch.setattr(worker, "call_ai", reply)


def test_worker_persists_versioned_evidence_and_attempt(question_job, monkeypatch):
    case_id, job_id, factory = question_job
    install_reply(monkeypatch)
    _, token = claim(factory)
    assert worker.process_job(job_id, token)
    with factory() as db:
        case, job = db.get(Case, case_id), db.get(Job, job_id)
        assert case.status == "answered"
        assert case.answer == "Test fixture answer."
        assert case.cite_pages == [115]
        assert case.answer_payload["manual"]["manual_version"] == "test-v1"
        assert case.answer_payload["steps"][0]["source_ids"] == [case.sources[0]["chunk_id"]]
        assert job.status == "completed" and job.claim_token is None
        assert db.get(JobAttempt, token).status == "completed"


def test_unclaimed_or_duplicate_execution_does_not_call_ai(question_job, monkeypatch):
    _, job_id, factory = question_job
    async def forbidden(*args):
        pytest.fail("An unowned execution called AI")
    monkeypatch.setattr(worker, "call_ai", forbidden)
    assert not worker.process_job(job_id, "wrong-token")
    assert not worker.process_job(job_id, None)
    _, token = claim(factory)
    install_reply(monkeypatch)
    assert worker.process_job(job_id, token)
    monkeypatch.setattr(worker, "call_ai", forbidden)
    assert not worker.process_job(job_id, token)


def test_busy_retries_on_schedule_then_completes(question_job, monkeypatch):
    case_id, job_id, factory = question_job
    install_reply(monkeypatch, 429, {"detail": "busy"}, {"Retry-After": "2"})
    _, token = claim(factory)
    assert not worker.execute_claimed_job(job_id, token)
    with factory() as db:
        job = db.get(Job, job_id)
        assert job.status == "pending" and job.next_run_at is not None
        assert db.get(Case, case_id).answer is None
        assert db.get(JobAttempt, token).error_code == "busy"
        assert worker.claim_next_pending_job(db) is None
        job.next_run_at = utcnow() - timedelta(seconds=1)
        db.commit()
    install_reply(monkeypatch)
    _, second = claim(factory)
    assert worker.execute_claimed_job(job_id, second)
    with factory() as db:
        assert db.get(Job, job_id).generation == 2
        assert len(db.execute(select(JobAttempt)).scalars().all()) == 2


def test_bad_evidence_is_terminal_without_a_fake_answer(question_job, monkeypatch):
    case_id, job_id, factory = question_job
    install_reply(monkeypatch, body={"answer": "uncited model output"})
    _, token = claim(factory)
    assert not worker.execute_claimed_job(job_id, token)
    with factory() as db:
        assert db.get(Case, case_id).answer is None
        assert db.get(Job, job_id).status == "failed"
        assert db.get(JobAttempt, token).error_code == "invalid_result_or_internal_error"


def test_healthy_heartbeat_preserves_lease_and_expired_attempt_is_fenced(question_job, monkeypatch):
    case_id, job_id, factory = question_job
    _, old = claim(factory)
    with factory() as db:
        job = db.get(Job, job_id)
        job.claimed_at = utcnow() - timedelta(hours=1)
        db.commit()
        assert worker.recover_abandoned_jobs(db) == 0
        job.heartbeat_at = utcnow() - timedelta(hours=1)
        db.commit()
        assert worker.recover_abandoned_jobs(db) == 1
    _, new = claim(factory)
    assert new != old
    assert not worker.heartbeat(job_id, old)
    assert not worker.mark_job_failed(job_id, "stale error", old)
    install_reply(monkeypatch)
    assert not worker.process_job(job_id, old)
    assert worker.process_job(job_id, new)
    with factory() as db:
        assert db.get(JobAttempt, old).status == "expired"
        assert db.get(Case, case_id).status == "answered"


def test_result_arriving_after_reclaim_cannot_overwrite_new_owner(question_job, monkeypatch):
    _, job_id, factory = question_job
    _, old = claim(factory)
    new_token = []

    async def late_reply(url, payload, budget):
        with factory() as db:
            job = db.get(Job, job_id)
            job.heartbeat_at = utcnow() - timedelta(hours=1)
            db.commit()
            worker.recover_abandoned_jobs(db)
        new_token.append(claim(factory)[1])
        return httpx.Response(200, request=httpx.Request("POST", url), json=make_answer())
    monkeypatch.setattr(worker, "call_ai", late_reply)
    assert not worker.process_job(job_id, old)
    with factory() as db:
        assert db.get(Job, job_id).claim_token == new_token[0]
        assert db.get(Job, job_id).status == "claimed"


def test_retry_budget_exhausts_and_preserves_attempts(question_job):
    _, job_id, factory = question_job
    for _ in range(worker.settings.rag_max_attempts):
        _, token = claim(factory)
        worker.mark_job_failed(
            job_id, "offline", token, error_code="connection_error", retryable=True)
        with factory() as db:
            job = db.get(Job, job_id)
            job.next_run_at = utcnow() - timedelta(seconds=1)
            db.commit()
    with factory() as db:
        assert db.get(Job, job_id).status == "failed"
        attempts = db.execute(select(JobAttempt)).scalars().all()
        assert len(attempts) == worker.settings.rag_max_attempts
