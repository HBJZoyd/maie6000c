# Model 3 Manual Assistant

## Final milestone

Start the final review at [submissions/week13/README.md](submissions/week13/README.md).
It indexes the technical brief, demo runbook, presentation and verification evidence.
Run `scripts\start.cmd -Mode Demo` for the recorded Sentry Mode presentation at
http://localhost:8030/app. The API, PostgreSQL and worker execute normally while
the inference boundary replays a dated answer. The AutoDL deployment remains the
real-model path. See the report for the scope of each evidence set.

Team **Odie**, course **MAIE6000C: Engineering AI Products — From Prototype to Production**.
MAIE6000C is the course name. This independent student prototype does not control
a vehicle or claim affiliation with Tesla.

The browser submits a question to FastAPI. One PostgreSQL transaction saves the
question and pending job before HTTP 202. A worker claims the job, invokes the RAG
boundary and saves the answer, steps, evidence excerpts and terminal state.
History survives application restart.

## Start without AutoDL — Windows CMD

Requirements: Docker Desktop's Linux engine, Docker Compose 2.24.4+ and PowerShell.
Initial builds download images/packages. No GPU, SSH or AutoDL is needed to use
the explicitly synthetic engineering environment:

~~~cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
scripts\start.cmd
~~~

Open **http://localhost:8020/app**. Its banner and results identify offline fixture
mode: **no real AI is called and no factual vehicle instructions are provided**.
The default project is odie-offline, with separate PostgreSQL and result-cache
volumes. Existing .env, W07 data and historical tags are preserved.

~~~cmd
docker --context default compose -p odie-offline -f compose.offline.yaml stop
~~~

Run the start command again to resume with saved history. Deleting volumes is not
a normal stop operation.

## Real AI deployment

The real backend uses the provisioned Chinese manual, BM25 + Milvus Lite hybrid
retrieval, BGE reranking and a local vLLM Qwen3 model on AutoDL. Its private model,
manual, index and MongoDB assets are not in Git. The reference environment is an
A100 40 GB and a separate Python 3.12 GPU environment; local containers use 3.11.

The new gateway requires an asset manifest and contract-v2 modules. Follow
[the current deployment runbook](docs/reliability-upgrade.md) to inventory/export
assets, verify them, start supervised dependencies and establish the SSH tunnel.
After the real backend is ready:

~~~cmd
scripts\start.cmd -Mode Remote
~~~

This starts the existing maie6000c project using configured ports (normally
http://localhost:8000/app). Do not run an old CLI and gateway together on one GPU.
Real GPU startup, JSON generation quality and fresh-GPU reproduction remain
pending verification while AutoDL is unavailable. Fixture checks do not establish
real-AI readiness. No automatic fixture fallback is used for failed real requests.

## Verification

Run the isolated unit, integration and real PostgreSQL suite:

~~~cmd
docker --context default compose -p odie-verification -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker --context default compose -p odie-verification -f compose.test.yaml down
~~~

With the offline application running, a standard-library Python 3.11+ interpreter
can verify HTTP, SQL persistence, PDF identity and restart recovery:

~~~cmd
python scripts\verify_offline.py --restart
~~~

The report identifies synthetic mode and real_ai_verified=false.
Unit tests use labelled fixtures and SQLite; PostgreSQL-specific tests use only
TEST_POSTGRES_URL with temporary schemas. They skip explicitly if it is absent.
CI and compose.test.yaml enable these tests. Real-model smoke tests remain opt-in.

## Documentation

- [Architecture](docs/architecture.md) and [decision records](docs/adrs/)
- [Operations](docs/operations.md)
- [Upgrade, startup and evidence-contract details](docs/reliability-upgrade.md)
- [Historical W07 report and real-AI evidence](submissions/week07/README.md)
- [Pre-existing RAG source and asset provenance](RAG/PROVENANCE.md)

## Source and supported scope

services/api serves HTTP/UI, services/worker executes jobs, services/ai
preserves the AI service boundary, and services/common contains persistence,
schemas and configuration. scripts/rag_gateway.py is the remote adapter, with
shared pure-Python evidence, asset and result-store helpers. Alembic migrations
extend existing data without resetting it. RAG source predates the integration;
local source changes are distinct from unchanged W07 remote snapshots.

Supported scope is single-user, single-manual, single-turn questions with history,
bounded retries and auditable evidence. Saved history is not multi-turn dialogue.
There is no measured factual-accuracy score, multi-vehicle version selection,
public-user authentication or automated safety decision-making. The legacy
/cases and /triage keyword example remains separate from manual RAG.
