from __future__ import annotations

from services.common.models import Case, CaseStatus, Job, JobStatus

import httpx


def test_question_is_queued_and_separate_from_legacy_cases(client, db_session):
    legacy = client.post("/cases", json={"title": "Legacy case", "description": "Keep this flow."})
    assert legacy.status_code == 201
    response = client.post("/questions", json={"question": "  Model 3 哨兵模式怎么用？  "})
    assert response.status_code == 202
    question = response.json()
    assert question["question"] == "Model 3 哨兵模式怎么用？"
    assert question["status"] == "queued"
    assert question["answer"] is None
    assert question["cite_pages"] == []
    job = db_session.get(Job, question["job_id"])
    assert job.job_type == "answer_question"
    assert [item["id"] for item in client.get("/questions").json()] == [question["id"]]
    assert client.get(f"/questions/{legacy.json()['case']['id']}").status_code == 404


def test_answer_and_sources_survive_api_read(client, db_session):
    created = client.post("/questions", json={"question": "Model 3 如何设置充电上限？"}).json()
    case = db_session.get(Case, created["id"])
    case.status = CaseStatus.ANSWERED.value
    case.answer = "根据已引用手册的内容回答。"
    case.cite_pages = [115, 116]
    case.sources = [{"page": 115, "excerpt": "手册原文"}]
    case.related_images = []
    job = db_session.get(Job, created["job_id"])
    job.status = JobStatus.COMPLETED.value
    db_session.commit()
    result = client.get(f"/questions/{created['id']}").json()
    assert result["answer"] == case.answer
    assert result["cite_pages"] == [115, 116]
    assert result["sources"][0]["excerpt"] == "手册原文"


def test_retry_only_failed_questions_and_reuses_one_job(client, db_session):
    question = client.post("/questions", json={"question": "哨兵模式如何关闭？"}).json()
    path = f"/questions/{question['id']}/retry"
    assert client.post(path).status_code == 409
    case = db_session.get(Case, question["id"])
    job = db_session.get(Job, question["job_id"])
    case.status = CaseStatus.FAILED.value
    job.status = JobStatus.FAILED.value
    job.error = "服务暂时不可用"
    job.attempts = 3
    db_session.commit()
    response = client.post(path)
    assert response.status_code == 202
    assert response.json()["job_id"] == question["job_id"]
    assert response.json()["status"] == "queued"
    assert response.json()["error"] is None
    assert response.json()["attempts"] == 0
    assert client.post(path).status_code == 409


def test_invalid_question_and_unsafe_image_path(client):
    for question in ("", "   ", "ok", "x" * 4001):
        assert client.post("/questions", json={"question": question}).status_code == 422
    assert client.get("/questions/not-a-question").status_code == 404
    assert client.get("/manual-images/not-an-image").status_code == 404


def test_idempotent_submission_and_conflicting_reuse(client):
    headers = {"Idempotency-Key": "test-submit-1"}
    body = {"question": "Model 3 哨兵模式如何开启？"}
    first = client.post("/questions", json=body, headers=headers)
    second = client.post("/questions", json=body, headers=headers)
    assert first.json()["id"] == second.json()["id"]
    assert client.post("/questions", json={"question": "different question"},
                       headers=headers).status_code == 409
    assert client.get(f"/questions/{first.json()['id']}/attempts").json() == []


def test_question_page_and_assets_are_packaged(client):
    page = client.get("/app")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "Model 3" in page.text
    for path in ("/assets/app.js", "/assets/style.css"):
        assert client.get(path).status_code == 200


def test_saved_manual_link_rejects_a_different_pdf_version(client, monkeypatch):
    from services.api.app import main as api
    monkeypatch.setattr(api, "fetch_manual_asset", lambda path: httpx.Response(
        200, content=b"%PDF-test", headers={"X-Document-SHA256": "f" * 64}))
    assert client.get("/manual.pdf?sha256=" + "f" * 64).status_code == 200
    assert client.get("/manual.pdf?sha256=" + "a" * 64).status_code == 409
