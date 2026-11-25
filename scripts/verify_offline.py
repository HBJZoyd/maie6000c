"""Exercise the running synthetic system, SQL persistence and optional clean restart."""

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8020")
    parser.add_argument("--project", default="odie-offline")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("artifacts/w13-offline/system.json"))
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]+", args.project):
        parser.error("Invalid project name")
    base = args.base_url.rstrip("/")

    def request(path, body=None, key=None):
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Idempotency-Key"] = key
        req = Request(base + path, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
        with urlopen(req, timeout=5) as response:
            return response.status, json.load(response)

    status = request("/system/status")[1]
    if status.get("mode") != "fixture" or status.get("rag") != "ready":
        raise RuntimeError("Refusing to run: expected a healthy, explicitly synthetic backend")
    body = {"question": "离线工程验证：哨兵模式如何开启？"}
    key = "offline-" + uuid.uuid4().hex
    code, accepted = request("/questions", body, key)
    assert code == 202
    assert request("/questions", body, key)[1]["id"] == accepted["id"]
    question_id = str(uuid.UUID(accepted["id"]))
    deadline = time.monotonic() + 45
    while True:
        answer = request("/questions/" + question_id)[1]
        if answer["status"] in {"answered", "failed"}:
            break
        if time.monotonic() > deadline:
            raise TimeoutError("Offline task did not finish")
        time.sleep(0.2)
    assert answer["status"] == "answered"
    assert answer["provenance"]["mode"] == "fixture"
    assert "模拟" in answer["answer"]
    attempts = request(f"/questions/{question_id}/attempts")[1]
    assert attempts and attempts[-1]["status"] == "completed"
    with urlopen(base + "/manual.pdf?sha256=" + answer["manual"]["document_sha256"],
                 timeout=5) as response:
        pdf = response.read()
    assert hashlib.sha256(pdf).hexdigest() == answer["manual"]["document_sha256"]

    compose = ["docker", "--context", "default", "compose", "-p", args.project, "-f",
               str(Path(__file__).resolve().parents[1] / "compose.offline.yaml")]
    sql_check = (
        "import json,sys; from services.common.db import get_session_factory; "
        "from services.common.models import Case; "
        "db=get_session_factory()(); c=db.get(Case,sys.argv[1]); "
        "print(json.dumps(c.answer_payload,ensure_ascii=False)); db.close()"
    )
    saved = subprocess.run(compose + ["exec", "-T", "api", "python", "-c", sql_check,
                                     question_id], check=True, capture_output=True, text=True,
                           encoding="utf-8")
    snapshot = json.loads(saved.stdout)
    validate_payload(snapshot)
    assert snapshot["answer"] == answer["answer"]
    if args.restart:
        subprocess.run(compose + ["restart"], check=True, timeout=60)
        deadline = time.monotonic() + 60
        while True:
            try:
                status = request("/system/status")[1]
                if status.get("rag") == "ready" and status.get("mode") == "fixture":
                    break
            except (HTTPError, URLError, TimeoutError, ConnectionError):
                pass
            if time.monotonic() > deadline:
                raise TimeoutError("Offline services did not recover after restart")
            time.sleep(0.5)
        restored = request("/questions/" + question_id)[1]
        assert restored["answer"] == answer["answer"]
        assert restored["manual"] == answer["manual"]
        assert request(f"/questions/{question_id}/attempts")[1] == attempts
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "mode": "fixture",
              "real_ai_verified": False, "input": body, "accepted": accepted,
              "answer": answer, "attempts": attempts, "sql_answer_payload": snapshot,
              "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
              "restart_verified": args.restart, "idempotency_verified": True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Offline HTTP/SQL/worker/evidence verification passed; restart={args.restart}")
    print(f"Report: {args.output}. Real AI was not invoked.")


if __name__ == "__main__":
    main()
