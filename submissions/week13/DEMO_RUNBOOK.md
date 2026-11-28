# Final Demonstration Runbook

Team Odie. Suggested format: four minutes of presentation and four minutes of
system demonstration. This duration is a recommendation, not an assignment rule.

## 1. Start the recorded presentation

Use Docker Desktop's Linux engine, the default context and Compose 2.24.4+.
From Windows CMD:

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
scripts\start.cmd -Mode Demo
```

Open http://localhost:8030/app. Select **哨兵模式演示**, then send the standard
question. The connection indicator and result identify a dated answer replay.
API submission, SQL storage, worker execution and result validation run normally.

A self-contained visual walkthrough is in SIMULATED_DEMO.html. Open that file
locally to present captured evidence without sending new requests. The application
is the interactive system; the HTML is a recorded explanation of one run.

For a clean clone on Linux/macOS, copy .env.example to .env, then run:

```sh
docker --context default compose -p odie-demo -f compose.demo.yaml up -d --build --wait
```

The demo includes its small recording and source packet in Git. It does not load
private model assets. The original AutoDL adapter remains the real-model deployment
path, documented in docs/reliability-upgrade.md. No automatic fallback connects
these two modes.

## 2. Present the system path

| Step | Operator action | Evidence |
|---|---|---|
| Input | Send the Sentry Mode question | HTTP 202 and saved question ID |
| Persistence | Pause the demo worker before submitting another copy | cases queued, jobs pending, empty result |
| Async work | Start the same worker | Claim and completion JSON events |
| AI boundary | Show the recorded answer entering the current contract | Recorded mode, source IDs and envelope |
| Output | Read saved answer and source packet | SQL answer_payload, two excerpts and attempt record |
| Operations | Show readiness, metrics and logs | Health response and job/attempt IDs |
| Recovery | Restart the project and reopen the same question | Identical saved answer and history |

Say once at the start: "This demonstration replays a recorded answer at the AI
boundary. The API, database and worker execute normally." Explain product behavior
through the rest of the flow without repeatedly narrating infrastructure setup.

## 3. Show queued and completed SQL

Stop only the dedicated demo worker, then submit the standard question in the UI:

```cmd
docker --context default compose -p odie-demo -f compose.demo.yaml stop worker
docker --context default compose -p odie-demo -f compose.demo.yaml exec -T db psql -U postgres -d maie6000c -c "SELECT id,status FROM cases ORDER BY created_at DESC LIMIT 3; SELECT id,case_id,status,attempts,generation FROM jobs ORDER BY id DESC LIMIT 3;"
docker --context default compose -p odie-demo -f compose.demo.yaml start worker
docker --context default compose -p odie-demo -f compose.demo.yaml logs --tail 40 worker
```

After completion, inspect the result and attempt history:

```cmd
docker --context default compose -p odie-demo -f compose.demo.yaml exec -T db psql -U postgres -d maie6000c -c "SELECT id,status,answer_payload IS NOT NULL AS has_result FROM cases ORDER BY created_at DESC LIMIT 3; SELECT generation,status,error_code FROM job_attempts ORDER BY started_at DESC LIMIT 5;"
curl.exe -f http://localhost:8030/health/ready
curl.exe -f http://localhost:8030/system/status
curl.exe -f http://localhost:8030/metrics
```

The two-page PDF is an excerpt packet. Its pages 1/2 correspond to original manual
pages 39/115 shown in source titles; do not present it as the complete manual.

## 4. Out-of-recording scenario

Click **不支持的问题** and send it. The system saves the question and completes
the job with a clear scope response, empty sources and no invented answer.
The captured example is evidence/replay/out-of-scope.json.

## 5. Restart recovery

After a question finishes:

```cmd
docker --context default compose -p odie-demo -f compose.demo.yaml restart
```

Wait for /health/ready, reopen the same question and show unchanged answer,
source identity and attempt history. Normal stop retains data:

```cmd
docker --context default compose -p odie-demo -f compose.demo.yaml stop
```

## 6. Collect fresh evidence

The collector uses a Python 3.11+ standard-library interpreter on the Docker host
only to orchestrate HTTP and Docker commands. The application and tests remain
inside Docker. It installs no host application environment.

```cmd
python scripts\collect_final_evidence.py --mode fixture --base-url http://127.0.0.1:8030 --project odie-demo --compose-file compose.demo.yaml --pause-worker --restart --output artifacts\w13-final\replay
```

It records replay provenance, queued/completed SQL, attempts, logs, metrics,
PDF identity and restart checks. Run stop/restart flags during a quiet demo window.
For a real-model verification run, use --mode live with the separately configured
real deployment. The collector rejects a mismatch between requested and actual mode.

## 7. Controlled failure and honest trade-off

During a quiet rehearsal, stop the demo RAG service, submit a question and inspect
safe errors and bounded retry scheduling. Restore it; if the retry budget is
exhausted, use the saved question's retry button. History remains durable.

```cmd
docker --context default compose -p odie-demo -f compose.demo.yaml stop rag
docker --context default compose -p odie-demo -f compose.demo.yaml start rag
```

The main trade-offs are at-least-once inference, single-manual/local-user scope
and the difference between reference integrity and semantic correctness. The
recorded run does not establish fresh model quality or model latency.
