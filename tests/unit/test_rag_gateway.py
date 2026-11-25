from pathlib import Path
from threading import Event, Thread

from fastapi.testclient import TestClient

from scripts.rag_gateway import ManualPipeline, create_app
from tests.rag_fixtures import make_answer


class FakePipeline:
    mode = "fixture"
    fingerprint = "test-backend-v1"

    def __init__(self):
        self.calls = 0

    def answer(self, query):
        self.calls += 1
        return make_answer()

    def image_path(self, image_id):
        return None


def test_gateway_auth_validation_and_durable_replay(tmp_path):
    pipeline = FakePipeline()
    body = {"query": "哨兵模式怎么用？", "case_id": "one-question"}
    headers = {"Authorization": "Bearer test-secret"}
    for _ in range(2):
        with TestClient(create_app(pipeline, tmp_path, api_token="test-secret")) as client:
            assert client.get("/health/ready").status_code == 401
            assert client.get("/health/ready", headers=headers).json()["mode"] == "fixture"
            response = client.post("/rag/query", json=body, headers=headers)
            assert response.status_code == 200
            assert response.json()["cite_pages"] == [115]
            invalid = client.post("/rag/query", json={"query": "   "}, headers=headers)
            assert invalid.status_code == 422
            assert client.get("/rag/manual", headers=headers).status_code == 404
            assert client.get("/rag/images/bad-id", headers=headers).status_code == 404
    assert pipeline.calls == 1
    pipeline.fingerprint = "test-backend-v2"
    with TestClient(create_app(pipeline, tmp_path, api_token="test-secret")) as client:
        assert client.post("/rag/query", json=body, headers=headers).status_code == 200
    assert pipeline.calls == 2


def test_gateway_does_not_expose_errors_or_accept_invalid_evidence(tmp_path):
    class BrokenPipeline(FakePipeline):
        def answer(self, query):
            raise RuntimeError("secret backend detail")
    with TestClient(create_app(BrokenPipeline(), tmp_path, api_token="")) as client:
        response = client.post("/rag/query", json={"query": "Model 3 哨兵模式"})
        assert response.status_code == 502 and "secret" not in response.text

    class InvalidPipeline(FakePipeline):
        def answer(self, query):
            return {"answer": "uncited output"}
    with TestClient(create_app(InvalidPipeline(), tmp_path, api_token="")) as client:
        response = client.post("/rag/query", json={"query": "Model 3 哨兵模式"})
        assert response.status_code == 502
        assert response.headers["X-RAG-Retryable"] == "false"


def test_busy_has_retry_after_and_does_not_drop_completed_cache(tmp_path):
    started, finish = Event(), Event()
    class SlowPipeline(FakePipeline):
        def answer(self, query):
            if query == "slow question":
                started.set()
                assert finish.wait(5)
            return super().answer(query)
    with TestClient(create_app(SlowPipeline(), tmp_path, api_token="")) as client:
        cached = {"query": "cached question", "case_id": "cached"}
        assert client.post("/rag/query", json=cached).status_code == 200
        thread = Thread(target=lambda: client.post(
            "/rag/query", json={"query": "slow question", "case_id": "slow"}))
        thread.start()
        try:
            assert started.wait(3)
            assert client.post("/rag/query", json=cached).status_code == 200
            busy = client.post("/rag/query", json={"query": "another question"})
            assert busy.status_code == 429 and busy.headers["Retry-After"] == "2"
        finally:
            finish.set()
            thread.join(5)


def test_dependency_failure_is_not_ready(tmp_path):
    pipeline = FakePipeline()
    pipeline.ready = lambda: False
    with TestClient(create_app(pipeline, tmp_path, api_token="")) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503


def test_image_registry_rejects_paths_outside_manual_data(tmp_path):
    pipeline = ManualPipeline.__new__(ManualPipeline)
    pipeline.root, pipeline.images = tmp_path, {}
    outside = tmp_path / "private.jpg"
    outside.write_bytes(b"private")
    assert pipeline.image_record({"image_path": str(outside), "page": 1}) is None
    data = tmp_path / "data/saved_images"
    data.mkdir(parents=True)
    image = data / "page1_img1.jpg"
    image.write_bytes(b"image")
    record = pipeline.image_record({"image_path": str(image), "page": 1, "title": "diagram"})
    assert record["title"] == "diagram" and len(record["id"]) == 32
    pipeline.images = {}
    assert pipeline.image_path(record["id"]) == Path(image)


def test_relocated_asset_snapshot_maps_only_its_old_data_directory(tmp_path):
    pipeline = ManualPipeline.__new__(ManualPipeline)
    old_root = tmp_path.parent / "legacy-rag-root"
    pipeline.root, pipeline.images = tmp_path, {}
    pipeline.manifest = {"source_root": str(old_root), "index_version": "test-release"}
    data = tmp_path / "data/saved_images"
    data.mkdir(parents=True)
    image = data / "page1_img1.jpg"
    image.write_bytes(b"image")
    record = pipeline.image_record({
        "image_path": str(old_root / "data/saved_images/page1_img1.jpg"), "page": 1})
    assert pipeline.image_path(record["id"]) == image
    assert pipeline.image_record({"image_path": str(old_root / "private.jpg"), "page": 1}) is None
