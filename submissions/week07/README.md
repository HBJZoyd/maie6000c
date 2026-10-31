# W07 Midterm Milestone Demo: Model 3 Manual Assistant

**Team: Odie. Course: MAIE6000C. Evidence date: 31 October 2026 (Hong Kong).**
Repository: https://github.com/HBJZoyd/maie6000c
Required checkpoint tag: `w07-midterm`.
Primary artifact: `submissions/week07/README.md`.

## 1. What currently works

A real browser question enters a FastAPI API, commits a PostgreSQL question and
job, passes through an asynchronous worker and local AI gateway, invokes the
existing AutoDL GPU RAG pipeline, and returns a saved answer with manual page
references, excerpts and image metadata. Saved history remains visible on reload.
New answers and remote PDF/images require the active AutoDL backend and SSH tunnel.

The submitted [PowerPoint](Odie_W07_Midterm_Demo.pptx) is the demonstration artifact
under the instructor's 28/29 October clarifications. No separate live stage
presentation, recording or narration is required. The system path itself is real
and is supported by raw HTTP, SQL, worker and operational evidence, not slides alone.

## 2. Demonstrated system path

The actual test question was: **Model 3 如何开启哨兵模式？在家停车时可以自动关闭吗？**

Question ID: `a17d3240-be02-445c-84a6-10abd6690fd8`. Job ID: **9**.

| Requirement | Captured evidence | Result |
|---|---|---|
| Input enters system | [request-accepted.json](evidence/request-accepted.json) | HTTP 202, question saved |
| Persisted state change | [database-queued.json](evidence/database-queued.json) | SQL confirms queued question and pending job |
| Async worker step | [state-timeline.json](evidence/state-timeline.json), [service-logs.txt](evidence/service-logs.txt) | processing/claimed observed; job_claimed logged |
| Persisted output | [database-answered.json](evidence/database-answered.json), [answer.json](evidence/answer.json), [job.json](evidence/job.json) | answered/completed, citations [39, 115] |
| Operational signal | [system-status.json](evidence/system-status.json), [api-metrics.txt](evidence/api-metrics.txt), [compose-ps.txt](evidence/compose-ps.txt) | API, SQL and RAG ready; worker completion logged |

The worker was deliberately stopped briefly to capture a stable committed queued
SQL snapshot, then restarted. This is a controlled evidence capture, not an
uninterrupted production latency benchmark. Job timestamps give queue **1.92s**,
processing **4.30s**, total **6.22s** for this one warm-service run.
Timing is not an average, percentile, SLA or answer-quality score.

PDF and two image routes returned HTTP 200; byte counts and media types are in
[asset-checks.json](evidence/asset-checks.json). Those images are associated with
retrieved pages; their semantic relevance has not been validated. The screenshot
does not establish correctness for every detail of the generated answer.

## 3. Current implementation status

**Implemented:** dedicated `/questions` API, static Chinese UI, PostgreSQL
persistence and additive migration, worker job claim and result writeback,
AutoDL HTTP adapter, cited results, history, explicit failed state, manual retry,
stale-claim recovery, loopback bindings, health/status endpoints and request logs.

**Partially implemented:** manual evidence linkage, model-quality validation,
operational visibility, GPU concurrency control. The pipeline can cite evidence,
but relevant retrieval, accurate citation support and correct images need a labelled
evaluation set. The gateway serializes inference and has a bounded process cache.

**Not implemented:** external-user authentication/isolation, retention policy,
automatic safety escalation, per-vehicle/year/software manual selection,
distributed tracing, comprehensive worker metrics, high availability, controlled
accuracy evaluation and repeatable load benchmarks.

## 4. Architecture and change since Week 04

The local boundary now explicitly uses `/questions` and `answer_question` jobs,
with dedicated answer and evidence fields. The legacy triage example remains
separate. The GPU code stays on the already-provisioned AutoDL instance rather
than becoming a heavy local Compose service. The real LLM client uses local vLLM
Qwen3 int4, and the vector store uses Milvus Lite. Details and diagrams are in
[architecture.md](../../docs/architecture.md).

The original RAG source and prepared model/index assets predate this integration.
Their provenance and omitted runtime assets are documented in
[RAG/PROVENANCE.md](../../RAG/PROVENANCE.md). The actual remote core files were read
over SSH; snapshots and SHA-256 values are in `evidence/autodl-source/` and
[autodl-runtime.json](evidence/autodl-runtime.json). No original inference or
model/index files were modified on AutoDL during this W07 preparation.

## 5. Testing and validation

| Check | Result | Evidence and boundary |
|---|---|---|
| Unit and integration suite | 18 passed | [Text](evidence/unit-integration-results.txt), [JUnit](evidence/unit-integration-junit.xml); SQLite isolation and explicit pipeline fixtures |
| Running-service smoke suite | 2 passed | [Text](evidence/smoke-results.txt), [JUnit](evidence/smoke-junit.xml); legacy triage plus real AutoDL charging question |
| Ruff on submitted application code | Passed | [lint-results.txt](evidence/lint-results.txt); pre-existing RAG snapshot excluded |
| Real Sentry Mode path | Completed | HTTP, PostgreSQL SQL snapshots, worker logs, pages 39/115 |
| Manual PDF and images | 3 HTTP 200 responses | [asset-checks.json](evidence/asset-checks.json) |

Tests cover schema/input handling, cited result persistence, gateway token
validation, bounded idempotent caching, safe image identifiers, hidden backend
errors, failure recording, retry restrictions and stale worker recovery.
Two dependency deprecation warnings remain. The live smoke tests verify integration
and persisted citations. They do not certify answer accuracy or safety.

## 6. Risks and revised scope

| Risk | Current handling | Remaining work |
|---|---|---|
| AutoDL/SSH outage | Explicit unavailable/failed status, durable history, retry | Supervised deployment and dependency-aware readiness |
| Incorrect retrieval or generation | Page links and visible source excerpts | Labelled questions, citation-support review and version matching |
| Single GPU / overload | Serial inference lock, 429, persisted jobs | Capacity measurement, queue policy and bounded retry/backoff |
| Privacy and public access | Local prototype with loopback-bound application ports | Authentication, user isolation and retention/deletion rules |
| Crash/replay | PostgreSQL jobs and stale lease recovery | Durable inference idempotency and stronger concurrency review |
| Reproduction assets | Source and setup documented, provisioned backend used | Model/data artifact manifest and portable authorized provisioning |

Biggest scope cut: retain one Chinese manual and one provisioned GPU backend.
Do not claim multi-vehicle coverage, vehicle control, a public multi-user service
or automated safety decisions. If capacity slips, defer image relevance improvements
and extra UI features while preserving the cited text workflow and evaluation.

## 7. Prioritized second-half plan

| Period | Work | Completion evidence |
|---|---|---|
| W08–W09 | Build a version-labelled question set and review retrieval/citation support; improve readiness and worker visibility | Human-reviewed answer/source set, failure scenarios and traceable job IDs |
| W10 | Add access controls, user isolation and retention rules before any external trial | Authentication/isolation tests and documented data lifecycle |
| W11 | Measure warm/cold latency and concurrent load; tune queue/backoff and retrieval only from results | Repeatable benchmark procedure, latency distribution and quality comparison |
| W12 | Rehearse clean restart, recovery and deployment using an asset manifest | Fresh-environment runbook and backup/recovery evidence |
| W13 | Freeze scope, finalize tests and technical brief/postmortem | Reproducible final checkpoint and honest remaining limitations |

These are planned outcomes, not claims of completed work or measured improvements.

## 8. Reproduce and review

Follow [docs/operations.md](../../docs/operations.md) and the exact
[demo runbook](DEMO_RUNBOOK.md). For the existing deployment, open
`http://localhost:8000/app`, inspect the saved Sentry question, open pages 39/115,
and correlate job 9 with the SQL and logs. A fresh run uses
`python scripts/collect_week07_evidence.py --output artifacts/new-week07-evidence`.
It needs the provisioned GPU backend; model/data assets and passwords are not bundled.

## 9. Artifact index

- [PowerPoint demonstration](Odie_W07_Midterm_Demo.pptx)
- [Demo runbook](DEMO_RUNBOOK.md)
- [Submission commands and Canvas format](SUBMIT_COMMANDS.md)
- `assets/app-ready.jpg`, `assets/sentry-answer.jpg`, `assets/manual-source.jpg`
- `evidence/` contains raw machine-readable records, test reports, logs and source snapshots.

## 10. Checkpoint and submission status

The required tag is `w07-midterm`. The authoritative submitted revision is the
commit resolved by that tag, not the latest moving branch. The local
`CANVAS_SUBMISSION.txt` records the actual tag SHA after the commit exists,
avoiding a self-referential SHA in this README. Use `git rev-parse` to verify that
SHA before submission. Push the branch and tag using the standard Git commands
in [SUBMIT_COMMANDS.md](SUBMIT_COMMANDS.md).
No Canvas submission or remote Git publication is implied by a local report.

## Requirement sources

- [Current W07 assignment and rubric](https://canvas.ust.hk/courses/74201/assignments/461342)
- [28 October PPT clarification](https://canvas.ust.hk/courses/74201/announcements/652340)
- [29 October documentation/evidence clarification](https://canvas.ust.hk/courses/74201/announcements/652495)

The W07 deadline is 31 October 2026 at 17:30 Hong Kong time. The available-until
date of 7 November is distinct from the due date. This is separate from the earlier
industry-expert elevator pitch assignment.
