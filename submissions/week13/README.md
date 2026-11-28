# W13 Final Team Project: Model 3 Manual Assistant

**Team Odie** · **MAIE6000C** · Submission account **C0216RC / RUICHAO CHEN**

Required checkpoint: `w13-final`. Primary artifact: this report.

## Product and delivered scope

The Model 3 Manual Assistant helps owners and support staff locate instructions
in a Chinese owner manual and inspect the source behind an answer. It joins a
browser, FastAPI, PostgreSQL, a separate worker and the AutoDL RAG service. Users
submit questions, inspect saved answers with references and revisit history after restart.

The core path developed at W07 remains browser, API, relational storage, worker,
AI boundary and persisted result. Final work strengthens ownership, retries,
versioned evidence and repeatability. It does not replace the underlying
retrieval/model architecture with another model.

Delivered scope: one Chinese manual, local single-user access, single-turn
questions and saved history. History is not conversational memory. Vehicle
control, public accounts and multiple vehicle versions are outside this scope.

## Repeatable simulated demonstration

With Docker Desktop's Linux engine running, use Windows CMD:

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
scripts\start.cmd -Mode Demo
```

Open **http://localhost:8030/app**, select **哨兵模式演示**, then send:

> Model 3 如何开启哨兵模式？在家停车时可以自动关闭吗？

The API, PostgreSQL, worker, result validation and operational signals execute
normally. At the inference boundary, the demo replays the answer recorded on
**31 October 2026**. The UI and persisted provenance identify this recorded mode.
This is a controlled presentation of the engineering workflow, rather than a
measurement of new retrieval, generation or factual accuracy.

Two source excerpts accompany the answer. Demo PDF pages 1 and 2 correspond to
original manual pages 39 and 115, retained in source titles. The two-page packet
is labelled demonstration material. Unrecorded questions receive a clear scope
response rather than the Sentry Mode answer.

[SIMULATED_DEMO.html](SIMULATED_DEMO.html) provides a self-contained, step-by-step
walkthrough of the captured Docker run. It displays evidence without sending new
requests. Use the running Docker application for the interactive demonstration.

## Seven-step review sequence

1. Submit the standard question and show HTTP 202.
2. Pause the demo worker and inspect the committed queued question and pending job.
3. Start the worker and correlate its claim and completion events.
4. Show the recorded answer passing through the current AI service boundary.
5. Inspect the saved answer, source excerpts and attempt history.
6. Show readiness, JSON logs and metrics, then restart the containers.
7. Reopen the same question and explain the recording and factual-support boundary.

Exact commands and the failure/recovery sequence are in [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md).

## Course contract and evidence

| Requirement | Delivered implementation | Evidence |
|---|---|---|
| Relational persistence | PostgreSQL cases, jobs, attempts and Alembic | Queued/completed SQL snapshots and concurrency tests |
| API/service layer | FastAPI, browser assets and separate AI HTTP service | HTTP 202, saved reads and integration tests |
| Worker/async path | Separate process, ownership tokens, heartbeat and bounded retries | Attempt records, JSON events and recovery tests |
| AI-enabled function | BM25 + Milvus Lite, BGE reranking, Qwen3/vLLM on AutoDL | Dated W07 real inference and current recorded presentation adapter |
| Reproducible local startup | Docker default, isolated demo project, pinned images and locks | Fresh demo volumes, startup and restart verification |
| Tests / verification | Unit, integration and real PostgreSQL suite | [Validation record](evidence/validation.json) |
| Documentation | Architecture, operations, ADRs and final materials | [Rubric map](RUBRIC_MAP.md) |
| Structured logs | Job and attempt IDs in JSON events | [Worker events](evidence/replay/worker-events.jsonl) |
| Health checks | Process liveness, SQL readiness and backend status | /health/live, /health/ready, /system/status |
| Observability | Route-based HTTP metrics and durable attempt history | [Metrics](evidence/replay/api-metrics.txt) |

## Validation scope

The final tests run inside Docker with CPython 3.11 and PostgreSQL 16. They cover
concurrent workers/submissions, idempotency, heartbeat, stale owners, retries,
migrations, source integrity and recorded-mode safeguards. The validation record
contains actual counts and commands, accompanied by Ruff and JavaScript checks.

The captured demo proves persistence before worker execution, stored output,
source-packet identity, operational signals and history after full container
restart. A second question verifies the out-of-recording response. Current demo
results carry `mode=fixture` and `demo_kind=recorded-replay`. W07's real-model
records remain dated and unchanged in `submissions/week07/evidence/`.

Reference integrity does not prove semantic entailment. New model quality,
live-model latency, user time savings and production uptime are not measured by
this recorded demonstration. [EVALUATION.md](EVALUATION.md) defines the separate
factual evaluation protocol.

## Architecture and trade-offs

See [architecture](../../docs/architecture.md), [operations](../../docs/operations.md)
and [ADRs](../../docs/adrs/). PostgreSQL keeps input/job creation atomic with few
services. Fenced ownership protects saved results, while inference can repeat
around a crash. The recorded adapter is explicitly selected in a separate project
and cannot silently replace the real backend.

The main limits are one manual, local single-user access, no public authentication,
no complete distributed trace and no measured semantic-quality benchmark. A public
pilot requires identity controls, quotas, retention and factual evaluation. The
product does not control a vehicle or certify driving safety.

## Semester progression

| Milestone | Commit | Development |
|---|---|---|
| Initial template | 482eb74 | API, AI service, database and worker baseline |
| W03 | 3999fae | Readiness work |
| W04 | 085885e | Architecture proposal |
| W07 | b099735 | Integrated manual Q&A and real inference evidence |
| Reliability | b6c5ef3 | Ownership, retries, versioned evidence and isolated startup |
| W13 | Resolve w13-final | Final materials, recorded demo and repeatable evidence |

The final branch descends from earlier milestones. Historical tags remain fixed.

## Final artifact index

- [Technical brief and postmortem](final-technical-brief.md)
- [Rubric map](RUBRIC_MAP.md)
- [Demo runbook](DEMO_RUNBOOK.md)
- [Simulated walkthrough](SIMULATED_DEMO.html)
- [Presentation](Odie_W13_Final_Demo.pptx)
- [Speaker script and Chinese rehearsal notes](SPEAKER_SCRIPT.md)
- [Evaluation protocol](EVALUATION.md)
- [GitHub/Canvas handoff](SUBMISSION.md)
- [Validation record](evidence/validation.json)

The slides support the system demonstration. They do not replace it.
