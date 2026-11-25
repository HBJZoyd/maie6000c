import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from scripts.fixture_rag import FixturePipeline
from scripts.rag_gateway import create_app


def test_offline_gateway_is_labelled_and_pdf_identity_is_checked(tmp_path):
    pipeline = FixturePipeline(tmp_path)
    with TestClient(create_app(pipeline, tmp_path, api_token="")) as client:
        assert client.get("/health/ready").json()["mode"] == "fixture"
        payload = client.post("/rag/query", json={"query": "test question"}).json()
        assert payload["provenance"]["mode"] == "fixture"
        assert "模拟" in payload["answer"]
        pdf = client.get("/rag/manual")
        assert pdf.content.startswith(b"%PDF")
        assert pdf.headers["X-Document-SHA256"] == payload["manual"]["document_sha256"]
        (tmp_path / "data/Tesla_Manual.pdf").write_bytes(b"changed")
        assert client.get("/rag/manual").status_code == 409


def test_fixture_mode_is_rejected_in_production(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "scripts.rag_gateway", "--mode", "fixture",
         "--rag-dir", str(tmp_path)], env=dict(os.environ, APP_ENV="production"),
        capture_output=True, timeout=10,
    )
    assert result.returncode != 0
    assert b"forbidden in production" in result.stderr


def test_asset_only_preflight_does_not_load_gpu_modules(tmp_path):
    from scripts.rag_assets import capture
    data = tmp_path / "data"
    data.mkdir()
    (data / "Tesla_Manual.pdf").write_bytes(b"test-only")
    manifest = capture(tmp_path, "test-v1", paths=["data/Tesla_Manual.pdf"], page_count=1)
    (tmp_path / "asset-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.start_rag", "--root", str(tmp_path),
         "--check-assets-only"], capture_output=True, timeout=10,
    )
    assert result.returncode == 0
    assert b"Verified assets" in result.stdout
