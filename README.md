# Tesla Model 3 Manual Q&A — RAG + Async Processing Architecture

## 1. Project Introduction

This project is a Retrieval-Augmented Generation (RAG) question-answering system built on an asynchronous processing architecture. It allows Tesla Model 3 owners to ask natural-language questions about vehicle operation and receive concise, cited answers sourced from the official owner's manual.

The system follows a three-service architecture:

- **API Service** (port 8000) — receives user questions, creates cases and background jobs, returns processed results
- **AI Service** (port 8100) — calls the RAG service to generate answers, returns labels/summaries/confidence
- **Worker** — polls pending jobs, claims and processes them, calls the AI service, writes results back to the database
- **RAG Service** (port 6001) — encapsulates the full retrieval-augmented generation pipeline: BM25 recall, Milvus hybrid search, BGE-M3 reranking, and LLM generation

The business flow: user submits a question via `POST /cases` → API writes case (status=`queued`) + job (status=`pending`) to PostgreSQL → Worker claims the job → calls AI Service → AI Service calls RAG → RAG retrieves relevant manual passages and generates a cited answer → Worker writes `ai_label`/`ai_summary`/`ai_confidence` back to the case → case status becomes `triaged`.

## 2. Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose)
- `.env` file configured (copy from `.env.example`)

### Start the Starter Stack

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start all services (db + ai + api + worker)
docker compose up --build

# 3. Optional: enable observability profile (Prometheus)
docker compose --profile observability up --build
```

### Verify the Stack

```bash
# Check API health
curl http://localhost:8000/health/ready

# Create a case (starts the workflow)
curl -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -d '{"title":"How to enable auto-lock","description":"When I walk away from the car, it does not lock automatically."}'

# Check worker logs
docker logs -f maie6000c-worker-1

# Query final state via API
curl http://localhost:8000/cases/<CASE_ID>
```

### Stop the Stack

```bash
# Stop and remove containers
docker compose down --remove-orphans

# Stop and remove volumes (full reset)
docker compose down -v --remove-orphans
```

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Service | FastAPI + Uvicorn | HTTP endpoints for case CRUD and job queries (port 8000) |
| AI Service | FastAPI + Uvicorn | Internal AI gateway, calls RAG service (port 8100) |
| RAG Service | FastAPI + Uvicorn | RAG pipeline: retrieval + reranking + LLM generation (port 6001) |
| Worker | Python polling loop | Async job processing, claim → process → complete/fail |
| Database | PostgreSQL 16 | Relational persistence for `cases` and `jobs` tables |
| ORM/Migration | SQLAlchemy 2.0 + Alembic | Model definitions and schema migrations |
| Vector Store | Milvus | BGE-M3 dense+sparse hybrid vector search |
| Document Store | MongoDB 7.0 | Storage for manual document chunks and metadata |
| Sparse Retrieval | BM25 (jieba + pickle) | Keyword-based recall as supplement to vector search |
| Reranker | BGE-M3 (Qwen3-Reranker) | Fine-grained relevance scoring of retrieved passages |
| LLM | Doubao API (OpenAI-compatible) | Answer generation with retrieved context |
| Deployment | Docker Compose | Reproducible local multi-service orchestration |
| Testing | pytest | Unit, integration, and smoke tests |
| Observability | Prometheus + structured logging | Metrics, health checks, structured JSON logs |

## 4. Directory Structure

```text
maie6000c/
│
├─ services/                     # ── Starter services ──
│  ├─ api/app/main.py             #   API service (port 8000)
│  ├─ ai/app/main.py              #   AI service (port 8100)
│  ├─ worker/app/main.py          #   Worker process (polling loop)
│  └─ common/                     #   Shared code (models, db, config, schemas)
│
├─ alembic/                       # ── Database migrations ──
│  └─ versions/                   #   Migration scripts
│
├─ tests/                         # ── Test suite ──
│  ├─ unit/                       #   Unit tests (AI logic)
│  ├─ integration/                #   Integration tests (API + DB)
│  └─ smoke/                      #   Smoke tests (end-to-end against running stack)
│
├─ docs/                          # ── Documentation ──
│  ├─ architecture.md             #   Architecture (English)
│  ├─ architecture_zh.md           #   Architecture (Chinese)
│  ├─ operations.md               #   Operations manual
│  └─ adrs/                       #   Architecture Decision Records
│
├─ submissions/                   # ── Milestone submissions ──
│  ├─ week03/                     #   Individual readiness lab
│  └─ week04/                     #   Team architecture proposal
│
├─ compose.yaml                   # Docker Compose orchestration
├─ Dockerfile                     # Python 3.11-slim image
├─ pyproject.toml                 # Python project config (deps, ruff, pytest)
├─ Makefile                       # Shortcut commands
└─ README.md                      # This file
│
├─ RAG/                           # ── RAG subsystem (separate) ──
│  ├─ infer.py                     #   Interactive RAG pipeline (CLI)
│  ├─ build_index.py               #   Build BM25 + Milvus indexes
│  ├─ config.ini                   #   RAG configuration
│  ├─ data/                        #   Tesla Manual PDF + stopwords
│  ├─ models/                      #   Pretrained models (Qwen3-8B, BGE-M3)
│  ├─ mongodb-7.0.20/              #   Standalone MongoDB binaries
│  └─ src/
│     ├─ retriever/                #   BM25/Milvus/FAISS/TF-IDF retrievers
│     ├─ reranker/                 #   BGE-M3/Qwen3 rerankers
│     ├─ client/                   #   LLM clients (chat/clean/hyde/local)
│     ├─ parser/                   #   PDF parsing + image handling
│     ├─ server/                   #   Semantic chunk service (port 6000)
│     └─ utils.py                  #   Utility functions
│
└─ observability/                 # ── Observability config ──
   └─ prometheus.yml               #   Prometheus scrape config
```

### Starter vs RAG

| Aspect | Starter (`services/`, `alembic/`, `tests/`) | RAG (`RAG/`) |
|--------|---------------------------------------------|--------------|
| Purpose | Async job processing architecture | Knowledge retrieval and answer generation |
| Database | PostgreSQL (cases, jobs) | MongoDB (documents), Milvus (vectors) |
| Services | API, AI, Worker | RAG service, semantic chunk service |
| Dependencies | FastAPI, SQLAlchemy, psycopg | BM25, Milvus, BGE-M3, LLM API |
| Integration | AI Service calls RAG via `POST /rag/query` | RAG returns answer/label/confidence |

## 5. Core Features

### Asynchronous Case Processing

- `POST /cases` creates a case (status=`queued`) and a job (status=`pending`) in one transaction
- Worker polls pending jobs, claims them (status=`claimed`), and processes them outside the request cycle
- Results are written back asynchronously; the API returns immediately without waiting for AI processing

### RAG-Powered Answer Generation

- BM25 sparse retrieval (keyword recall) + Milvus hybrid search (BGE-M3 dense+sparse)
- RRF merge and dedup of multi-source retrieved passages
- BGE-M3 reranker for fine-grained relevance scoring
- LLM generates cited answers using retrieved manual context
- Answer, label, confidence, and source citations persisted to the case

### State Management

| Entity | States | Flow |
|--------|--------|------|
| Case | `queued` → `triaged` / `failed` | Created → AI processed → success or failure |
| Job | `pending` → `claimed` → `completed` / `failed` | Created → worker claimed → done or error |

### Health Checks & Observability

- Liveness and readiness probes for all services (`/health/live`, `/health/ready`)
- Prometheus metrics endpoints (`/metrics`)
- Structured JSON logging with context fields (`job_id`, `case_id`, `label`)
- Optional observability profile for Prometheus dashboard

### Database Migration

- Alembic-managed schema migrations with version control
- Initial migration creates `cases` and `jobs` tables
- Run migrations: `docker compose run --rm api alembic upgrade head`

### Testing

- **Unit tests**: AI triage logic (`tests/unit/test_ai_service.py`)
- **Integration tests**: Case/Job creation and retrieval (`tests/integration/test_api_case_flow.py`)
- **Smoke tests**: End-to-end flow against running stack (`tests/smoke/test_smoke_cases.py`)

```bash
# Run unit + integration tests
pytest -q

# Run smoke tests against a running stack
SMOKE_BASE_URL=http://localhost:8000 pytest tests/smoke -q
```
