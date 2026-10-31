from pathlib import Path

from fastapi.testclient import TestClient

from scripts.rag_gateway import ManualPipeline, create_app


class FakePipeline:
    def __init__(self):
        self.calls = 0

    def answer(self, query):
        self.calls += 1
        return {
            "answer": "这是测试夹具的答案，不是模型生成。",
            "cite_pages": [115],
            "sources": [{"page": 115, "excerpt": query}],
            "related_images": [],
        }

    def image_path(self, image_id):
        return None


def test_gateway_auth_validation_and_inference_idempotency(tmp_path):
    pipeline = FakePipeline()
    app = create_app(pipeline, tmp_path, api_token="test-secret")
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 401
        headers = {"Authorization": "Bearer test-secret"}
        assert client.get("/health/ready", headers=headers).json()["status"] == "ready"
        body = {"query": "哨兵模式怎么用？", "case_id": "one-question"}
        for _ in range(2):
            response = client.post("/rag/query", json=body, headers=headers)
            assert response.status_code == 200
            assert response.json()["cite_pages"] == [115]
        assert pipeline.calls == 1
        assert client.post("/rag/query", json={"query": "   "}, headers=headers).status_code == 422
        assert client.get("/rag/manual", headers=headers).status_code == 404
        assert client.get("/rag/images/bad-id", headers=headers).status_code == 404


def test_gateway_does_not_expose_inference_errors(tmp_path):
    class BrokenPipeline(FakePipeline):
        def answer(self, query):
            raise RuntimeError("secret backend detail")

    with TestClient(create_app(BrokenPipeline(), tmp_path, api_token="")) as client:
        response = client.post("/rag/query", json={"query": "Model 3 哨兵模式"})
        assert response.status_code == 502
        assert "secret" not in response.text


def test_image_registry_rejects_paths_outside_manual_data(tmp_path):
    pipeline = ManualPipeline.__new__(ManualPipeline)
    pipeline.root = tmp_path
    pipeline.images = {}
    outside = tmp_path / "private.jpg"
    outside.write_bytes(b"private")
    assert pipeline.image_record({"image_path": str(outside), "page": 1}) is None
    data = tmp_path / "data" / "saved_images"
    data.mkdir(parents=True)
    image = data / "page1_img1.jpg"
    image.write_bytes(b"image")
    record = pipeline.image_record({"image_path": str(image), "page": 1, "title": "diagram"})
    assert record["title"] == "diagram"
    assert len(record["id"]) == 32
    pipeline.images = {}
    assert pipeline.image_path(record["id"]) == Path(image)
