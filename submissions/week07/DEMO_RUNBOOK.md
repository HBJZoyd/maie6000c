# W07 evidence review and reproduction

Team Odie. Use the saved evidence for asynchronous review; no video is needed.

## Existing captured run

1. Read `evidence/request-accepted.json`: HTTP 202 returned for the Sentry question,
   ID `a17d3240-be02-445c-84a6-10abd6690fd8`, job `9`.
2. Read `evidence/database-queued.json`: direct PostgreSQL query confirms the input,
   queued question, pending job and empty answer before the worker proceeds.
3. Read `evidence/state-timeline.json` and filter `evidence/service-logs.txt` for
   `job_claimed` and `job_completed` with job `9`.
4. Read `evidence/database-answered.json` and `evidence/answer.json`: saved answer,
   pages 39/115 and source excerpts; `evidence/job.json` shows completed, attempts 1.
5. Inspect `evidence/system-status.json`, `compose-ps.txt` and `api-metrics.txt` for
   connectivity, service state and request observations. The capture time is in UTC;
   add eight hours for Hong Kong time.
6. Inspect `assets/sentry-answer.jpg` and `assets/manual-source.jpg`, then open the
   real `/app` history and page links if the instance is online.

## Create a new real demonstration

Follow the operations guide to start the local containers, AutoDL dependencies,
one gateway and one SSH tunnel. Then execute from the repository root:

```powershell
python scripts/collect_week07_evidence.py --output artifacts/new-week07-evidence
```

This intentionally stops the worker briefly to record committed queued state,
then restarts it in a finally block. It creates a new question and does not delete
existing questions. Allow up to 240 seconds and inspect failures rather than
substituting fixtures or editing the generated answer. The Python command needs
only the standard library. Docker and the actual services are prerequisites.

## Test replay

Use Python 3.11 and the root README's test commands. Set `SMOKE_BASE_URL` and
`SMOKE_MANUAL_RAG=1` to enable the true running-service charging-question test.
Failure, retry and stale lease behaviors have isolated automated contract tests;
the W07 capture does not claim a production outage exercise or a load benchmark.

## Interpretation limits

This one run has 1.92s from job creation to claim and 4.30s from
claim to completion, total 6.22s. Worker startup was deliberately controlled.
Use the raw timestamps and capture method, not this observation as an SLA. The
answer remains subject to manual/version checks. Citation and image presence
proves returned structure and accessibility, not semantic correctness.
