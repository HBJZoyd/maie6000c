# Final Technical Brief and Postmortem

Team Odie. MAIE6000C. Submission account: C0216RC / RUICHAO CHEN.

## Product and scope

The Model 3 Manual Assistant gives owners and support staff a question-answer
interface over a Chinese owner manual. It saves questions and answers, displays
source excerpts and ties results to a document identity. Scope is one manual,
single-turn questions and local browser access. Intended value is easier manual
navigation and source checking; business impact is not quantified.

## Stable core architecture

The core path remains the W07 architecture: browser, FastAPI, PostgreSQL, separate
worker, AI HTTP boundary and AutoDL RAG. The real pipeline combines BM25 and
Milvus Lite retrieval, parent-document merging, BGE reranking and Qwen3 generation
through vLLM. MongoDB supplies document records. Final changes concern adaptation,
task reliability, evidence contracts and repeatability rather than replacement
of the underlying retrieval or model architecture.

One SQL transaction commits the input and pending job before HTTP 202. The worker
claims a job, commits ownership before HTTP, calls the AI service, validates the
envelope and saves the terminal state. The browser reads persisted output.
Cases store input and answer envelopes; jobs store scheduling and ownership;
job_attempts store generations and outcomes. Additive migrations preserve earlier
data without inventing document metadata for historical records.

## Demonstration design

An explicitly selected recorded adapter in the odie-demo Docker project replays
the exact standard Sentry Mode question/answer recorded on 31 October 2026.
Submission, SQL persistence, worker execution, validation, logs, metrics and
recovery all execute against the current application.

The source packet has two demonstration pages containing saved excerpts. These
page numbers differ from original manual pages 39 and 115, retained in titles.
The packet and UI identify the recording. Unrecorded questions receive a scope
response without invented citations. Provenance remains fixture mode, and the
adapter is forbidden in production. No automatic real-to-recorded fallback exists.

This controls the presentation's inference boundary while exercising the actual
application path. The run measures engineering behavior and reference consistency,
not new retrieval, generation quality or live-model latency. ADR 0005 records
this decision alongside the earlier queue, evidence and deployment decisions.

## Reliability and maintainability

The PostgreSQL queue keeps input and job creation atomic without a separate
broker at this scale. Workers use SKIP LOCKED, unique claim tokens, increasing
generations and conditional heartbeats. Completion/failure verifies ownership
under lock before updating job, attempt and result together. Recovery fences
expired owners, preventing a late response from overwriting a newer attempt.

Transient failures receive bounded backoff with jitter; invalid evidence fails
immediately. Manual retries retain prior attempts. The gateway's durable SQLite
replay cache reduces repeated completed requests, but a crash before cache commit
can repeat inference. Execution is at least once with fenced application writes.

Shared schemas and persistence live in services/common. The gateway separates
asset validation, evidence checks and result replay. Image digests and dependency
locks support reproducibility. Separate demo, test and real deployments isolate
volumes. Normal shutdown retains history.

## AI and source integrity

The real model produces answer steps tied to retrieved source IDs. The gateway
rejects IDs outside the candidate set. The application validates page bounds,
manual identity/version, PDF hash, excerpt checksums and cited-step consistency
again. PDF requests reject a different document identity. Clarification and
insufficient-evidence outcomes remain distinct from answers.

The recorded adapter uses this same contract with explicit recorded provenance.
These checks protect references. Human review still determines whether a claim
follows from the full source context and applies to the user's vehicle.

## Evidence and validation

Docker tests cover unit behavior, service integration and real PostgreSQL.
Important risks include duplicate submissions, concurrent claims, heartbeat,
stale ownership, retry limits, corrupt references, migration preservation and
recorded-mode restrictions. The actual commands and results are indexed in
`evidence/validation.json`.

The captured Sentry Mode demo proves HTTP 202, queued SQL before worker execution,
claim/completion events, stored output, source-packet identity, metrics and restart
survival. A second question demonstrates the out-of-recording response. W07
independently documents earlier real inference. No accuracy percentage, uptime
SLO, live-model latency percentile or user study is inferred from this replay.

## Operations and boundaries

Docker default remains the local environment. The demo starts with
`scripts\start.cmd -Mode Demo` on port 8030. Liveness, SQL readiness, backend
status, JSON events, request metrics and attempt history support diagnosis.
Metrics use route templates rather than per-question UUID series. Process metrics
reset on restart; attempt history remains durable in SQL.

The local single-user prototype has no public accounts, identity-scoped quotas or
full distributed tracing. Credentials and private runtime assets stay outside Git.
A public pilot needs access controls, retention policy, reviewed factual quality
and explicit manual/version coverage.

## Postmortem and priorities

W07 integrated the terminal RAG prototype into an HTTP/browser workflow. The
reliability pass addressed the lifecycle around a model call: accepted inputs,
interrupted workers, retries, duplicate requests and source identity. The final
presentation makes that lifecycle reproducible through a fixed, dated example.

The key lesson is to keep application correctness and model quality separately
checkable. A reliably saved response still needs factual review. The presentation
therefore shows the user outcome together with its SQL state and operational evidence.

Next priorities are human-reviewed factual evaluation, repeatable real-model
runtime/asset checks, manual-version selection and public access controls before
voice input, conversation memory or a broader vehicle catalogue.
