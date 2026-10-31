"""Opt-in real AutoDL check. No test double or generated fixture is used here."""
import os
import time

import httpx
import pytest

pytestmark = pytest.mark.smoke


def test_real_manual_question_persists_cited_answer():
    base = os.environ.get("SMOKE_BASE_URL")
    if not base or os.environ.get("SMOKE_MANUAL_RAG") != "1":
        pytest.skip("Set SMOKE_BASE_URL and SMOKE_MANUAL_RAG=1 for the live GPU test")
    with httpx.Client(base_url=base, timeout=15, trust_env=False) as client:
        assert client.get("/system/status").json()["rag"] == "ready"
        response = client.post(
            "/questions", json={"question": "Model 3 如何设置充电上限和预约充电？"}
        )
        assert response.status_code == 202
        accepted = response.json()
        deadline = time.monotonic() + 210
        while time.monotonic() < deadline:
            result = client.get(f"/questions/{accepted['id']}").json()
            if result["status"] in {"answered", "failed"}:
                break
            time.sleep(0.5)
        assert result["status"] == "answered", result
        assert result["answer"] and result["cite_pages"] and result["sources"]
        assert client.get(f"/jobs/{accepted['job_id']}").json()["status"] == "completed"
        assert client.get(f"/questions/{accepted['id']}").json()["answer"] == result["answer"]
