"""Real PostgreSQL tests; only TEST_POSTGRES_URL and isolated temporary schemas are used."""

import os
import asyncio
import subprocess
import sys
import uuid
import time
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url

from services.api.app.main import app
from services.common.db import Base, get_db, make_session_factory
from services.common.models import Case, Job, JobAttempt
from services.worker.app import main as worker
from tests.rag_fixtures import make_answer


@pytest.fixture()
def pg_schema():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL not set; PostgreSQL concurrency not verified")
    schema = "odie_test_" + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    target = make_url(url).update_query_dict({"options": f"-csearch_path={schema}"})
    try:
        yield target
    finally:
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture()
def pg_factory(pg_schema):
    engine = create_engine(pg_schema)
    Base.metadata.create_all(engine)
    try:
        yield make_session_factory(engine)
    finally:
        engine.dispose()


def test_two_workers_complete_twenty_jobs_once(pg_factory, monkeypatch):
    monkeypatch.setattr(worker, "get_session_factory", lambda: pg_factory)
    async def reply(url, payload, budget):
        return httpx.Response(200, request=httpx.Request("POST", url), json=make_answer())
    monkeypatch.setattr(worker, "call_ai", reply)
    with pg_factory() as db:
        for i in range(20):
            case = Case(title=f"Question {i}", description="test fixture question", status="queued")
            db.add(case)
            db.flush()
            db.add(Job(case_id=case.id, job_type="answer_question", status="pending"))
        db.commit()

    def consume():
        claimed = []
        while True:
            with pg_factory() as db:
                job = worker.claim_next_pending_job(db)
            if job is None:
                return claimed
            claimed.append(job.id)
            assert worker.process_job(job.id, job.claim_token)

    with ThreadPoolExecutor(max_workers=2) as pool:
        groups = list(pool.map(lambda _: consume(), range(2)))
    ids = groups[0] + groups[1]
    assert len(ids) == len(set(ids)) == 20
    with pg_factory() as db:
        assert all(j.status == "completed" and j.attempts == 1
                   for j in db.execute(select(Job)).scalars())
        assert len(db.execute(select(JobAttempt)).scalars().all()) == 20


def test_concurrent_api_submission_reuses_one_committed_question(pg_factory):
    def override():
        with pg_factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            def submit(_):
                response = client.post("/questions", headers={"Idempotency-Key": "same-submit"},
                                       json={"question": "test fixture question"})
                assert response.status_code == 202
                return response.json()["id"]
            with ThreadPoolExecutor(max_workers=4) as pool:
                ids = list(pool.map(submit, range(8)))
            assert len(set(ids)) == 1
            assert client.post("/questions", headers={"Idempotency-Key": "same-submit"},
                               json={"question": "different question"}).status_code == 409
        with pg_factory() as db:
            assert len(db.execute(select(Job)).scalars().all()) == 1
    finally:
        app.dependency_overrides.clear()


def test_heartbeat_keeps_a_slow_active_attempt_owned(pg_factory, monkeypatch):
    monkeypatch.setattr(worker, "get_session_factory", lambda: pg_factory)
    monkeypatch.setattr(worker.settings, "rag_job_lease_seconds", 0.3)
    monkeypatch.setattr(worker.settings, "worker_heartbeat_seconds", 0.05)
    started, release = Event(), Event()
    async def slow_reply(url, payload, budget):
        started.set()
        assert await asyncio.to_thread(release.wait, 3)
        return httpx.Response(200, request=httpx.Request("POST", url), json=make_answer())
    monkeypatch.setattr(worker, "call_ai", slow_reply)
    with pg_factory() as db:
        case = Case(title="Slow question", description="fixture question", status="queued")
        db.add(case)
        db.flush()
        db.add(Job(case_id=case.id, job_type="answer_question", status="pending"))
        db.commit()
        job = worker.claim_next_pending_job(db)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker.process_job, job.id, job.claim_token)
        try:
            assert started.wait(2)
            time.sleep(0.45)
            with pg_factory() as db:
                current = db.get(Job, job.id)
                assert current.heartbeat_at > current.claimed_at
                assert worker.recover_abandoned_jobs(db) == 0
        finally:
            release.set()
        assert future.result(timeout=3)


def test_migration_preserves_w07_answer_and_supports_round_trip(pg_schema):
    env = dict(os.environ, DATABASE_URL=pg_schema.render_as_string(hide_password=False))
    def migrate(revision, command="upgrade"):
        subprocess.run([sys.executable, "-m", "alembic", command, revision], env=env,
                       cwd=Path(__file__).resolve().parents[2], check=True, capture_output=True)
    engine = create_engine(pg_schema)
    try:
        migrate("20261023_0002")
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO cases (id,title,description,status,answer,created_at,"
                              "updated_at) VALUES ('old','old title','old description','answered',"
                              "'saved W07 answer',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
        migrate("head")
        with engine.connect() as conn:
            row = conn.execute(text("SELECT answer,answer_payload FROM cases WHERE id='old'")).one()
            assert row == ("saved W07 answer", None)
        migrate("20261023_0002", "downgrade")
        migrate("head")
    finally:
        engine.dispose()
