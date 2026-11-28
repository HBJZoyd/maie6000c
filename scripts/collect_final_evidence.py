"""Capture a labelled final demo using HTTP, PostgreSQL, worker logs and metrics.

Run with a Python 3.11+ standard-library interpreter on the Docker host. Live mode
refuses fixtures. Optional worker stop/start and restart affect only the named
Compose project, preserve volumes, and must be used during a team demo window.
"""

import argparse
import hashlib
import json
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from scripts.rag_evidence import validate_payload
except ModuleNotFoundError:
    from rag_evidence import validate_payload


def require_mode(status, expected):
    if status.get("rag") != "ready" or status.get("mode") != expected:
        raise RuntimeError(f"Expected healthy {expected} backend, received {status}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["live", "fixture"], required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--compose-file", type=Path, required=True)
    parser.add_argument("--pause-worker", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument(
        "--question", default="Model 3 如何开启哨兵模式？在家停车时可以自动关闭吗？"
    )
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--output", type=Path, default=Path("artifacts/w13-final/demo"))
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]+", args.project):
        parser.error("Invalid Compose project name")
    if not args.compose_file.is_file() or not 1 <= args.timeout <= 1800:
        parser.error("Existing Compose file and timeout of 1..1800 seconds required")
    args.output.mkdir(parents=True, exist_ok=True)
    base = args.base_url.rstrip("/")
    compose = ["docker", "--context", "default", "compose", "-p", args.project,
               "-f", str(args.compose_file.resolve())]

    def run(*command):
        return subprocess.run(compose + list(command), check=True, capture_output=True,
                              text=True, encoding="utf-8", timeout=90).stdout

    def request(path, body=None, key=None):
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Idempotency-Key"] = key
        req = Request(base + path, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
        with urlopen(req, timeout=15) as response:
            content = response.read()
            if "application/json" in response.headers.get("Content-Type", ""):
                content = json.loads(content)
            return response.status, content

    def save(name, value):
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
        (args.output / name).write_text(text, encoding="utf-8")

    def sql_snapshot(question_id):
        code = (
            "import json,sys; from sqlalchemy import select; "
            "from services.common.db import get_session_factory; "
            "from services.common.models import Case,Job; "
            "db=get_session_factory()(); c=db.get(Case,sys.argv[1]); "
            "j=db.execute(select(Job).where(Job.case_id==c.id)).scalar_one(); "
            "print(json.dumps(dict(question_id=c.id,question_status=c.status,job_id=j.id,"
            "job_status=j.status,attempts=j.attempts,generation=j.generation,"
            "answer_payload=c.answer_payload),ensure_ascii=False)); db.close()"
        )
        return json.loads(run("exec", "-T", "api", "python", "-c", code, question_id))

    started = datetime.now(timezone.utc).isoformat()
    status = request("/system/status")[1]
    require_mode(status, args.mode)
    save("system-status.json", status)
    save("health.json", request("/health/ready")[1])
    if args.pause_worker:
        run("stop", "worker")
    try:
        key = "final-" + uuid.uuid4().hex
        code, accepted = request("/questions", {"question": args.question}, key)
        assert code == 202
        question_id = str(uuid.UUID(accepted["id"]))
        save("request-accepted.json", accepted)
        assert request("/questions", {"question": args.question}, key)[1]["id"] == question_id
        if args.pause_worker:
            queued = sql_snapshot(question_id)
            assert queued["question_status"] == "queued" and queued["job_status"] == "pending"
            assert queued["answer_payload"] is None
            save("database-queued.json", queued)
    finally:
        if args.pause_worker:
            run("start", "worker")
    deadline = time.monotonic() + args.timeout
    timeline = []
    while True:
        answer = request("/questions/" + question_id)[1]
        if not timeline or timeline[-1]["status"] != answer["status"]:
            timeline.append({"at": datetime.now(timezone.utc).isoformat(),
                             "status": answer["status"]})
            save("state-timeline.json", timeline)
        if answer["status"] in {"answered", "failed"}:
            save("answer.json", answer)
            break
        if time.monotonic() > deadline:
            raise TimeoutError("Demo question did not finish within the budget")
        time.sleep(0.5)
    assert answer["status"] == "answered", answer.get("error")
    assert answer["answer_type"] == "answered", "Use an answerable question for the core demo"
    assert answer["provenance"]["mode"] == args.mode
    persisted = sql_snapshot(question_id)
    validate_payload(persisted["answer_payload"])
    assert persisted["answer_payload"]["answer"] == answer["answer"]
    assert persisted["job_status"] == "completed"
    save("database-answered.json", persisted)
    attempts = request(f"/questions/{question_id}/attempts")[1]
    assert attempts and attempts[-1]["status"] == "completed"
    save("attempts.json", attempts)
    pdf = request("/manual.pdf?sha256=" + answer["manual"]["document_sha256"])[1]
    assert hashlib.sha256(pdf).hexdigest() == answer["manual"]["document_sha256"]
    save("api-metrics.txt", request("/metrics")[1].decode())
    logs = run("logs", "--no-color", "--tail", "500", "worker")
    # Keep only JSON events related to this demo. Never export environment dumps.
    job_text = f'"job_id": {accepted["job_id"]}'
    events = [line[line.index("{"):] for line in logs.splitlines()
              if "{" in line and (job_text in line or question_id in line)]
    assert any('"job_completed"' in line for line in events), "Missing worker completion log"
    save("worker-events.jsonl", "\n".join(events) + "\n")
    save("compose-ps.json", json.loads("[" + ",".join(
        run("ps", "--format", "json").strip().splitlines()) + "]"))
    if args.restart:
        run("restart")
        deadline = time.monotonic() + 90
        while True:
            try:
                require_mode(request("/system/status")[1], args.mode)
                break
            except (HTTPError, URLError, TimeoutError, ConnectionError, RuntimeError):
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)
        restored = request("/questions/" + question_id)[1]
        assert restored["answer"] == answer["answer"]
        assert restored["manual"] == answer["manual"]
        assert request(f"/questions/{question_id}/attempts")[1] == attempts
    report = {"started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
              "mode": args.mode, "real_ai_verified": args.mode == "live",
              "demo_kind": status.get("demo_kind"),
              "inference_execution": ("live_model" if args.mode == "live" else
                                      "recorded_response_replay" if
                                      status.get("demo_kind") == "recorded-replay" else
                                      "generated_fixture"),
              "factual_accuracy_evaluated": False, "question_id": question_id,
              "input_persisted_before_worker_verified": args.pause_worker,
              "restart_verified": args.restart, "idempotency_verified": True,
              "pdf_sha256": hashlib.sha256(pdf).hexdigest()}
    save("summary.json", report)
    save("manifest.json", {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(args.output.iterdir()) if p.name != "manifest.json"})
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
