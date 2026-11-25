# Architecture: Model 3 Manual Assistant

Team Odie, MAIE6000C. Current local implementation extends the W07 checkpoint.
Historical real-AI evidence remains in submissions/week07; current offline
verification does not repeat or replace that GPU evidence.

## System boundary and components

One versioned Chinese Model 3 manual supports single-turn information questions.
The system does not control vehicles or certify operational safety.

| Component | Responsibility |
|---|---|
| Browser + FastAPI | Submit, read history, distinguish answer types, open evidence |
| PostgreSQL 16 | Questions, jobs, generations, attempts and immutable answer envelopes |
| Worker | Conditional claim, heartbeat, bounded retry, fenced completion |
| AI HTTP gateway | Validate RAG contract and preserve retry/error semantics |
| Real RAG gateway | Retrieval, reranking, structured generation, evidence validation |
| vLLM / BGE / BM25 / Milvus Lite / MongoDB | Existing provisioned GPU pipeline |
| Gateway SQLite store | Bounded durable replay of completed inference results |
| SSH forwarding | Reach the loopback-bound real backend |

~~~mermaid
flowchart LR
    UI[Browser] -->|POST question and idempotency key| API[FastAPI]
    API -->|Commit input and pending job| DB[(PostgreSQL)]
    DB -->|Claim with token| W[Worker]
    W --> AI[AI HTTP gateway]
    AI -->|Real deployment: SSH tunnel| RAG[RAG gateway]
    RAG --> RET[BM25 and Milvus Lite]
    RET --> RR[BGE reranker]
    RR --> LLM[vLLM Qwen3]
    RAG <--> CACHE[(Durable result replay)]
    AI -->|Offline deployment only| F[Explicit synthetic fixture]
    W -->|Validate and conditionally save| DB
    UI -->|Read persisted result| API
~~~

The fixture is selected by a separate deployment, not by catching a real inference
failure. Readiness, answer provenance and UI identify fixture mode.

## Persistence and task ownership

1. One transaction creates a question and pending job before returning 202.
2. A unique optional submission key handles concurrent/repeat requests. Reuse with
   changed text returns 409. Keys are global in this single-user scope.
3. A worker locks the oldest eligible pending job with SKIP LOCKED, conditionally
   claims it, creates a UUID token and attempt row, and commits before HTTP.
   Generation remains monotonic across manual retries.
4. A conditional heartbeat keeps the lease alive during a wall-clock-bounded call.
5. Completion locks the job again and verifies status/token before committing
   question, evidence envelope, attempt and terminal job state together.
6. Recovery ends expired attempts and clears ownership before requeueing.
   Late completion/failure from an old token is discarded.

Lock order is Job then Case, including manual retry. Pending retries have a
scheduled time; busy/connection/timeout/transient-server errors use bounded backoff.
Invalid evidence is terminal. RAG_MAX_ATTEMPTS bounds automatic attempts.
Manual retry resets that budget while preserving all prior attempt records.

The Case table remains for compatibility. New answer_payload holds the complete
versioned envelope alongside legacy answer/pages/source fields. W07 rows remain
unversioned and readable. The additive 20261125_0003 migration adds submission keys,
fencing fields, scheduling and attempt records.

## RAG evidence contract

The gateway uses BM25 top-10 and Milvus hybrid top-10 candidates, merges parent
documents and reranks to five candidates. It assigns stable chunk IDs and asks the
model for JSON steps citing those exact IDs. Sources carry manual identity/version,
PDF hash, page, excerpt and excerpt checksum. Generation provenance identifies
model, index release, prompt and real/fixture mode.

The gateway rejects outside IDs, missing references, invalid pages and inconsistent
versions. The application validates envelope consistency again before persistence.
Clarification and insufficient-evidence outcomes complete jobs but are distinct
from answered results. Reference integrity does not establish semantic entailment
or factual accuracy. Human-labelled evaluation is still needed.

Completed results persist in a bounded SQLite replay store. Keys include question
identity/text and backend identity. A crash before cache commit can repeat GPU
work. This is at-least-once execution with fenced application writes.

## Startup and assets

Application/PostgreSQL images are pinned by digest; application/test transitive
dependencies are pinned separately. Offline and real deployments use different
projects/volumes. Migrations precede API startup; local dependency health controls
startup order.

A private manifest records manual/model/index/image/record hashes and GPU runtime
versions. MongoDB records can be exported and restored only into an empty target.
Real startup verifies the release and uses a working copy of Milvus Lite, preserving
the original index. The supervisor owns only processes it starts.

The gateway must be upgraded to contract v2 before new answers are accepted.
W07 snapshot files are historical evidence, not current deployment code.

## Operations and limitations

API/AI process health, SQL readiness, RAG dependency readiness and structured logs
are available. Job/attempt IDs and timestamps explain retry behavior. Full tracing
and idle-worker metrics are not implemented. PDF requests check document identity;
historical images from another index release may be unavailable instead of
silently resolving to newer assets.

See ADRs 0002–0004 for queue, evidence and startup choices. GPU bootstrap, memory
settings, model JSON compliance and factual quality still need remote verification.
Public access additionally needs authentication, isolation and quotas.
