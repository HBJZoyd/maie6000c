from datetime import timedelta

import httpx
import pytest

from services.common.db import make_session_factory
from services.common.models import Case, Job, utcnow
from services.worker.app import main as worker


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


def test_worker_calls_rag_and_persists_citations(question_job, monkeypatch):
    case_id, job_id, factory = question_job

    def answer(url, **kwargs):
        assert url.endswith("/rag/query")
        assert kwargs["json"] == {"case_id": case_id, "question": "哨兵模式怎么用？"}
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "answer": "Test fixture answer.",
                "cite_pages": [116, 115, 115],
                "sources": [{"page": 115, "excerpt": "Quoted test fixture"}],
                "related_images": [],
            },
        )

    monkeypatch.setattr(worker.httpx, "post", answer)
    with factory() as db:
        assert worker.claim_next_pending_job(db).id == job_id
    worker.process_job(job_id)
    with factory() as db:
        case = db.get(Case, case_id)
        job = db.get(Job, job_id)
        assert case.status == "answered"
        assert case.answer == "Test fixture answer."
        assert case.cite_pages == [115, 116]
        assert case.sources[0]["excerpt"] == "Quoted test fixture"
        assert case.ai_label is None
        assert job.status == "completed"
        assert job.attempts == 1


def test_worker_failure_is_recorded_without_a_fake_answer(question_job, monkeypatch):
    case_id, job_id, factory = question_job

    def unavailable(url, **kwargs):
        raise httpx.ConnectError("upstream offline")

    monkeypatch.setattr(worker.httpx, "post", unavailable)
    with pytest.raises(httpx.ConnectError):
        worker.process_job(job_id)
    worker.mark_job_failed(job_id, "车书问答服务未连接")
    with factory() as db:
        assert db.get(Case, case_id).status == "failed"
        assert db.get(Case, case_id).answer is None
        assert db.get(Job, job_id).error == "车书问答服务未连接"


def test_stale_worker_job_is_recovered_but_live_job_is_not(question_job):
    case_id, job_id, factory = question_job
    with factory() as db:
        job = worker.claim_next_pending_job(db)
        worker.recover_abandoned_jobs(db)
        assert job.status == "claimed"
        job.claimed_at = utcnow() - timedelta(hours=1)
        db.commit()
        worker.recover_abandoned_jobs(db)
        assert job.status == "pending"
        assert db.get(Case, case_id).status == "queued"
        job.status = "claimed"
        job.claimed_at = utcnow() - timedelta(hours=1)
        job.attempts = worker.settings.rag_max_attempts
        db.commit()
        worker.recover_abandoned_jobs(db)
        assert job.status == "failed"
        assert db.get(Case, case_id).status == "failed"
