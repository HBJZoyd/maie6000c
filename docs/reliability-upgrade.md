# W13 preparation: startup, reliable jobs and evidence integrity

This work extends W07 on branch `codex/w13-reliability`. W07 evidence and its tag
remain historical. No AutoDL instance was contacted or modified for this upgrade.
GPU startup, memory use and real-model JSON generation still need verification
when that backend becomes available. Engineering fixtures are explicitly labelled.

## Start without AutoDL (Windows CMD)

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
scripts\start.cmd
```

Open http://localhost:8020/app. This is a synthetic engineering environment using
real PostgreSQL, HTTP, two-stage job processing and persisted evidence-shaped test
results. It provides **no factual vehicle answers and makes no model calls**.
The page, result and backend status identify fixture mode. Initial image/dependency
downloads need internet; subsequent operation needs neither SSH nor AutoDL.
The separate project `odie-offline` and its own volumes preserve the old deployment.
Docker Compose 2.24.4+ is required for `!override` / `!reset` in the override file.

The wrapper creates `.env` from the example only if absent, validates Compose,
runs migrations and waits for local health. It never overwrites an existing `.env`.
For a different port use `scripts\start.cmd -ApiPort 8030`.

```cmd
docker --context default compose -p odie-offline -f compose.offline.yaml ps
docker --context default compose -p odie-offline -f compose.offline.yaml logs --tail 80 worker
docker --context default compose -p odie-offline -f compose.offline.yaml stop
```

Normal stop retains data. Start again to verify history survives. Do not use
`down -v` for normal shutdown. To exercise two worker processes:

```cmd
docker --context default compose -p odie-offline -f compose.offline.yaml up -d --scale worker=2
```

## Job protocol

HTTP 202 follows the transaction committing both question and job. An optional
`Idempotency-Key` (1–128 ASCII letters/digits/`._:-`) identifies one submission.
Reusing it with different text returns 409. A database uniqueness constraint also
handles concurrent requests. Keys are global within this single-user prototype;
external multi-user deployment requires identity-scoped keys and authorization.

Each claim creates a UUID token, increments a monotonic generation and writes a
`job_attempts` row. Completion and failure lock and check `claimed + claim_token`
before updating the question and job in one transaction. Late owners cannot write.
Heartbeat updates are conditional on that token. Recovery uses the last heartbeat
(or claim time for old W07 jobs), ends the expired attempt and fences its owner.

429, connection errors, timeouts and transient 502/503/504 responses receive bounded
exponential backoff with jitter. Retry-After is honored up to the configured maximum
delay. Invalid evidence and explicit non-retryable errors terminate immediately.
Each automatic attempt counts toward `RAG_MAX_ATTEMPTS`. Manual retry resets that
budget, while preserving the monotonic generation and all prior attempt records.
The worker enforces a wall-clock HTTP budget, independently of HTTP inactivity limits.

Inspect `/questions/{id}/attempts` for attempt IDs, status, time and safe error codes.
The remote SQLite store replays completed results across gateway restart. Its key
includes question ID, text and backend asset/prompt identity. It has bounded age and
size. A crash between inference and cache commit can repeat GPU work: this remains
at-least-once processing with fenced application writes, not exactly-once inference.

## Evidence contract v2

New answers require a manual ID/version, PDF SHA-256, page count, immutable excerpts,
excerpt checksums, stable evidence IDs, cited steps and generation provenance.
The gateway accepts only IDs in the exact retrieved candidate set. The application
checks version agreement, valid pages, checksums and step/evidence consistency again.
Unknown IDs, reference 0, out-of-range pages and missing references are rejected.

`answer_type` separates `answered`, `needs_clarification` and `insufficient_evidence`.
The last two complete the job but are shown distinctly in the UI without citations.
This verifies reference integrity; it does not establish semantic entailment or
vehicle safety. Human-labelled factual evaluation remains a separate final task.

The complete envelope is saved as `cases.answer_payload` alongside legacy fields.
Old W07 records remain readable with unknown version metadata; no metadata is
invented or backfilled. New PDF links include the expected hash: an incompatible
currently served manual returns 409 instead of silently opening another version.

## Prepare real GPU assets when available (not yet remotely verified)

Use a trusted copy of the manual, existing authorized model weights, BM25 and
Milvus Lite indexes, stopwords, images and MongoDB records. Git does not contain
these large/private runtime assets. Hashes establish identity, not download rights
or authenticity. Only load trusted pickle indexes. Copy this repository's current
RAG source and scripts to the GPU host, preserving the private assets separately.

The existing backend requirements snapshot is `RAG/requirements.txt`; the recorded
reference environment is Python 3.12 on an A100 40 GB. Package/CUDA compatibility on
a fresh GPU image remains unverified. The application containers use Python 3.11.
Do not merge the two Python environments or blindly upgrade the GPU environment.

With MongoDB running in the configured backend environment:

```bash
python /path/to/checkout/scripts/rag_assets.py export-mongo --root /path/to/RAG
python /path/to/checkout/scripts/rag_assets.py capture --root /path/to/RAG --manual-version ACTUAL_DOCUMENT_VERSION
python /path/to/checkout/scripts/start_rag.py --root /path/to/RAG --check-assets-only
```

Capture hashes every required file, including weights, and can take time. Preserve
the asset manifest and the exact captured files privately as an immutable release.
Stop writers while capturing indexes and exporting records; do not hash a live
changing Milvus database. `manual_text.jsonl` allows a fresh empty MongoDB collection
to be restored; restore refuses to overwrite a nonempty collection. The existing
source has fixed defaults, so the gateway maps configured root paths before import.

To manage MongoDB and vLLM when absent, and supervise the gateway:

```bash
python /path/to/checkout/scripts/start_rag.py --root /path/to/RAG --manage-services --mongod /absolute/path/to/mongod
```

The supervisor validates assets, checks CUDA, reuses healthy existing dependencies,
restores only an empty manual collection, and starts required child processes.
It binds managed services to loopback and writes logs under `RAG/runtime/`.
Ctrl+C stops only child processes it created. The GPU memory fraction is configurable
and needs measurement on the actual machine. Reconnect using `connect-rag.ps1` once
the new manifest and modules are deployed; it no longer supports a lone gateway file.
Milvus works on a runtime copy so the captured release database is preserved.

Real startup on Windows, after the backend/tunnel is available:

```cmd
scripts\start.cmd -Mode Remote
```

This uses the existing `maie6000c` deployment and its configured ports. Do not point
it at the offline fixture when recording real-AI evidence. A v1 gateway must be
upgraded before it can produce new v2 answers; old saved answers remain readable.
Remote startup stops existing workers before migrating/updating services, so old
unfenced W07 worker code is not mixed with the new protocol. Interrupted attempts
recover after their lease expires; no question data is deleted.

## Verification without a GPU

```cmd
docker --context default compose -p odie-verification -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker --context default compose -p odie-verification -f compose.test.yaml down
```

This creates a separate PostgreSQL test service, exposes no database host port, and
uses temporary schemas for concurrency/migration tests. It does not use live data.
Tests distinguish fixture integration from real AI. Without `TEST_POSTGRES_URL`,
the PostgreSQL-specific tests skip explicitly; CI and this Compose command set it.
After all offline checks pass, still run the real smoke suite and a fresh-environment
GPU rehearsal before claiming final complete-system reproducibility.

## Local verification completed on 25 November 2026

- 50 unit/integration/PostgreSQL tests passed, including concurrent submissions,
  two workers completing 20 jobs, active heartbeat, stale-owner fencing, bounded
  retries, evidence corruption rejection and migration round trips.
- Ruff, JavaScript syntax and PowerShell parsing passed. Two existing dependency
  deprecation warnings remain; there were no failed tests.
- The CMD wrapper started a new source directory with no .env and fresh, isolated
  database/cache volumes. The generated configuration and schema migrations worked.
- Real HTTP, PostgreSQL persistence, worker execution, synthetic PDF checksum and
  whole-stack restart/history checks passed in the explicitly synthetic deployment.
- Generated reports are local under artifacts/w13-offline and can be regenerated
  using the verification commands. They are not real-AI evaluation results.

Pending: transfer/deploy the new GPU modules, capture real asset/runtime identities,
rehearse fresh GPU startup, check memory allocation and model JSON compliance, then
run real-AI smoke tests and human-reviewed factual evaluation. No remote changes
or real-model verification are claimed by this offline pass.
