"""Capture a real HTTP/SQL/worker vertical slice without deleting existing data.

Run from the repository root with the real backend and default Docker context up.
The worker is stopped briefly to photograph the committed queued state, then
restarted in a finally block. Output contains only the new demonstration record.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def docker(*args):
    result = subprocess.run(
        ["docker", "--context", "default", "compose", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    return result.stdout


def http(base, path, payload=None):
    raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base + path, data=raw, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=210) as response:
        content = response.read()
        is_json = "json" in response.headers.get("Content-Type", "")
        return response.status, json.loads(content) if is_json else content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="submissions/week07/evidence")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    def save(name, data):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    started = datetime.now(timezone.utc).isoformat()
    _, status = http(args.base_url, "/system/status")
    if status.get("rag") != "ready":
        raise SystemExit("Real RAG backend must be ready before collecting evidence.")
    save("system-status.json", {"captured_at_utc": started, **status})
    (output / "compose-ps.txt").write_text(docker("ps"), encoding="utf-8")
    question = "Model 3 如何开启哨兵模式？在家停车时可以自动关闭吗？"
    timeline = []
    try:
        docker("stop", "worker")
        code, record = http(args.base_url, "/questions", {"question": question})
        assert code == 202 and record["status"] == "queued"
        save("request-accepted.json", {"http_status": code, "body": record})
        question_id, job_id = record["id"], record["job_id"]
        # UUID comes from our validated API response, not arbitrary SQL input.
        import uuid
        uuid.UUID(question_id)
        sql = (
            "SELECT json_build_object('case_id',c.id,'case_status',c.status,"
            "'question',c.description,'answer',c.answer,'cite_pages',c.cite_pages,"
            "'sources',c.sources,'job_id',j.id,'job_status',j.status,'attempts',j.attempts,"
            "'created_at',j.created_at,'claimed_at',j.claimed_at,'completed_at',j.completed_at) "
            f"FROM cases c JOIN jobs j ON j.case_id=c.id WHERE c.id='{question_id}';"
        )
        before = docker(
            "exec", "-T", "db", "psql", "-U", "postgres", "-d", "maie6000c", "-tA", "-c", sql
        )
        save("database-queued.json", json.loads(before))
    finally:
        docker("start", "worker")
    timer = time.monotonic()
    deadline = timer + 240
    last_status = None
    while time.monotonic() < deadline:
        _, record = http(args.base_url, f"/questions/{question_id}")
        _, job = http(args.base_url, f"/jobs/{job_id}")
        state = (record["status"], job["status"])
        if state != last_status:
            timeline.append({"observed_at_utc": datetime.now(timezone.utc).isoformat(),
                             "seconds_since_worker_start": round(time.monotonic() - timer, 3),
                             "case_status": state[0], "job_status": state[1]})
            last_status = state
        if record["status"] in {"answered", "failed"}:
            break
        time.sleep(0.3)
    save("state-timeline.json", {
        "method": "Worker briefly stopped for the queued SQL snapshot, then restarted.",
        "states": timeline,
    })
    save("answer.json", record)
    save("job.json", job)
    after = docker(
        "exec", "-T", "db", "psql", "-U", "postgres", "-d", "maie6000c", "-tA", "-c", sql
    )
    save("database-answered.json", json.loads(after))
    logs = docker("logs", "--no-color", "--since", started, "api", "ai", "worker")
    (output / "service-logs.txt").write_text(logs, encoding="utf-8")
    _, metrics = http(args.base_url, "/metrics")
    (output / "api-metrics.txt").write_bytes(metrics)
    checks = []
    with urllib.request.urlopen(args.base_url + "/manual.pdf", timeout=60) as response:
        checks.append({
            "asset": "/manual.pdf", "status": response.status,
            "bytes": len(response.read()), "content_type": response.headers.get("Content-Type"),
        })
    for image in record.get("related_images", [])[:2]:
        path = "/manual-images/" + image["id"]
        with urllib.request.urlopen(args.base_url + path, timeout=60) as response:
            checks.append({"asset": path, "status": response.status, "bytes": len(response.read()),
                           "content_type": response.headers.get("Content-Type")})
    save("asset-checks.json", checks)
    assert record["status"] == "answered", record
    assert record.get("answer") and record.get("cite_pages")
    assert job["status"] == "completed" and job["attempts"] >= 1
    summary = {"captured_at_utc": started, "case_id": question_id, "job_id": job_id,
               "status": record["status"], "cite_pages": record["cite_pages"],
               "source_count": len(record.get("sources", [])), "asset_checks": len(checks),
               "timing_note": "Single warm-service observation, not a benchmark."}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
