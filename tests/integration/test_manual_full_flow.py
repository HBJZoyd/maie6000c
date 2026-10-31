"""Contract test through all service boundaries using an explicit RAG fixture."""

from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from scripts.rag_gateway import create_app
from services.ai.app.main import app as ai_app
from services.common.db import make_session_factory
from services.worker.app import main as worker


def test_question_to_gateway_to_persisted_answer(client, db_session, monkeypatch, tmp_path):
    class PipelineFixture:
        def answer(self, question):
            assert question == "Model 3 哨兵模式如何开启？"
            return {
                "answer": "仅供接口测试的夹具答案。",
                "cite_pages": [115],
                "sources": [{"page": 115, "excerpt": "仅供测试的手册片段"}],
                "related_images": [],
            }

    factory = make_session_factory(db_session.bind)
    monkeypatch.setattr(worker, "get_session_factory", lambda: factory)
    gateway = create_app(PipelineFixture(), tmp_path, api_token="")
    with TestClient(gateway) as rag_client, TestClient(ai_app) as ai_client:

        def route_post(url, **kwargs):
            if urlsplit(url).port == 8100:
                return ai_client.post("/rag/query", json=kwargs["json"])
            return rag_client.post("/rag/query", json=kwargs["json"])

        monkeypatch.setattr(worker.httpx, "post", route_post)
        response = client.post("/questions", json={"question": "Model 3 哨兵模式如何开启？"})
        question = response.json()
        with factory() as db:
            job = worker.claim_next_pending_job(db)
            assert job.id == question["job_id"]
        worker.process_job(job.id)
        db_session.expire_all()
        answer = client.get(f"/questions/{question['id']}").json()
        assert answer["status"] == "answered"
        assert answer["answer"] == "仅供接口测试的夹具答案。"
        assert answer["cite_pages"] == [115]
        assert answer["sources"][0]["excerpt"] == "仅供测试的手册片段"
