# Model 3 Manual Assistant

A manual-grounded question-answering prototype with a browser UI, durable PostgreSQL
jobs, an asynchronous worker, and an existing GPU RAG pipeline hosted on AutoDL.
**Team: Odie. Course: MAIE6000C, Engineering AI Products: From Prototype to Production.**
MAIE6000C is the course name, not the product name. This student prototype is not
affiliated with Tesla and does not control a vehicle.

## Current working path

Open `http://localhost:8000/app`. The browser submits `POST /questions`. The API
commits a question and a pending job, then returns HTTP 202. The worker claims the
job, calls the local AI gateway, and that gateway calls AutoDL through SSH port
forwarding. The answer, citation pages, source excerpts, and image metadata are
committed to PostgreSQL and can be read from history.

The legacy `/cases` and `/triage` endpoints retain the starter's keyword triage
example for compatibility. They do **not** perform the manual RAG workflow.

## Quick start: Windows and the provisioned AutoDL instance

Requirements: Docker Desktop with its Linux engine running, OpenSSH, the existing
AutoDL `rag` Conda environment and provisioned manual/model/index assets. Local
application containers use Python 3.11. Large model weights, the manual PDF,
indexes, MongoDB data, private configuration, and passwords are not in Git.

In local PowerShell, from the repository root:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker --context default compose up -d --build --wait
```

In a separate SSH terminal, start dependencies **once after an AutoDL reboot**:

```bash
cd /root/autodl-tmp/RAG
source /root/miniconda3/etc/profile.d/conda.sh
source config.ini
curl -fsS http://127.0.0.1:8000/v1/models
```

`config.ini` is the existing private instance configuration. Inspect readiness
before starting duplicate processes. The semantic-chunk service is an indexing
dependency and is not required to answer against the existing indexes.

In a second local PowerShell terminal, start the gateway and SSH tunnel:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\connect-rag.ps1 -SshHost region-9.autodl.pro -Port 16814 -RemotePython /root/miniconda3/envs/rag/bin/python
```

Enter the password only at the SSH prompt. The process-specific execution policy
does not change the machine's permanent policy. Keep this terminal open. If a
gateway is already running on AutoDL, use the tunnel-only command in the operations
guide instead of launching another copy.

```powershell
Invoke-RestMethod http://localhost:8000/system/status
```

Expect `api`, `database`, and `rag` to be `ready`. Open `/app` and ask about Sentry
Mode. This check reports connectivity and initialized retrieval, not answer accuracy.

## Documentation and milestone entry points

- [Architecture and design decisions](docs/architecture.md)
- [Operations and troubleshooting](docs/operations.md)
- [Chinese startup walkthrough](docs/startup-zh.md)
- [W07 milestone report and evidence index](submissions/week07/README.md)
- [W07 demo runbook](submissions/week07/DEMO_RUNBOOK.md)
- [Pre-existing backend and assets](RAG/PROVENANCE.md)
- [Submission commands](submissions/week07/SUBMIT_COMMANDS.md)

## Tests

On a Python 3.11 development environment:

```powershell
python -m pip install -e '.[dev]'
python -m pytest -q tests/unit tests/integration
python -m ruff check .
```

For real running-service tests, including the GPU backend:

```powershell
$env:SMOKE_BASE_URL = 'http://localhost:8000'
$env:SMOKE_MANUAL_RAG = '1'
python -m pytest -q tests/smoke
```

The live suite creates demonstration records. Tests use SQLite fixtures for unit
and contract isolation, while the captured live workflow uses PostgreSQL and real
AutoDL inference. A live smoke test proves service integration, not factual accuracy.

## Source layout

`services/api` serves HTTP and static UI; `services/worker` runs jobs;
`services/ai` implements the HTTP boundary to RAG; `services/common` contains
models, schemas and configuration; `scripts/rag_gateway.py` wraps the existing
AutoDL pipeline; `alembic/versions` records database migrations; `RAG/src` and
`RAG/infer.py` retain the pre-existing backend source snapshot.

## Scope and limitations

This is a single-user engineering prototype. New answers and manual files require
the GPU backend and SSH tunnel; previously saved answer text and source excerpts
remain readable locally. There is no measured accuracy score, model confidence,
per-vehicle version matching, user authentication or automatic safety escalation.
Review safety-related questions with qualified personnel and the applicable manual.
