# Operations: local application and provisioned AutoDL backend

Team Odie. Verified environment: Windows Docker context `default`; AutoDL A100
40 GB; existing Conda environment `/root/miniconda3/envs/rag/bin/python`.
Credentials are supplied interactively. Never commit `.env`, SSH passwords,
private `RAG/config.ini`, model weights or live database directories.

## Start and check the local application

Start Docker Desktop and wait until `docker --context default info` succeeds.
From the repository root in PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker --context default compose up -d --build --wait
docker --context default compose ps
```

API startup runs `alembic upgrade head` automatically. Existing PostgreSQL volume
data is retained. Rebuild after source changes. Do not overwrite an existing `.env`.
The local RAG URL should be `http://host.docker.internal:6001`, not container
`localhost:6001`. API, AI and database host ports bind to loopback.

## Start the existing AutoDL dependencies after instance reboot

```powershell
ssh -p 16814 root@region-9.autodl.pro
```

Inside that remote Linux session:

```bash
cd /root/autodl-tmp/RAG
source /root/miniconda3/etc/profile.d/conda.sh
source config.ini
which python
curl -fsS http://127.0.0.1:8000/v1/models
python -c "from src.client.mongodb_config import MongoConfig; print(MongoConfig.get_db().command('ping'))"
```

Only source the instance configuration once when the dependencies are not running.
It starts MongoDB and vLLM; its sleeps do not establish actual model readiness.
The existing semantic-chunk process may fail independently; it is not on the
inference path when the BM25 and Milvus Lite indexes already exist. Avoid running
the CLI `infer.py` alongside the gateway because it loads a second set of GPU models.

## Gateway and forwarding: choose one mode

If no RAG gateway is running, use this in a new **local PowerShell** terminal:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\connect-rag.ps1 -SshHost region-9.autodl.pro -Port 16814 -RemotePython /root/miniconda3/envs/rag/bin/python
```

The script uploads the adapter and starts one remote foreground gateway plus the
tunnel. Keep that terminal open. It does not overwrite `infer.py`, indexes or models.

For the W07 evidence session, a gateway was started in the background on AutoDL.
When that gateway is still healthy, use **tunnel only** in a local terminal:

```powershell
ssh -N -p 16814 -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:6001:127.0.0.1:6001 root@region-9.autodl.pro
```

Do not run both tunnel modes on the same local port. To start the background mode
after confirming no gateway exists, in the remote `rag` shell:

```bash
cd /root/autodl-tmp/RAG
nohup /root/miniconda3/envs/rag/bin/python maie_rag_gateway.py --rag-dir /root/autodl-tmp/RAG --port 6001 >> log/maie_gateway-w07.log 2>&1 < /dev/null &
```

This survives an SSH shell closing but not an AutoDL instance shutdown. It is not
a supervised production service. Models, prepared indexes and MongoDB must already
be provisioned. The local clone alone cannot recreate proprietary/runtime assets.

## Readiness, evidence and manual checks

```powershell
Invoke-RestMethod http://127.0.0.1:6001/health/ready
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:8000/system/status
docker --context default compose logs --tail 80 api ai worker
```

`/health/ready` on the API checks PostgreSQL. `/system/status` additionally asks the
AI gateway about RAG readiness. The RAG readiness response indicates initialized
retrieval; verify `/v1/models` and one genuine question for full-path confidence.
The AI service's own health response only confirms its process.

Open `http://localhost:8000/app` and ask a Sentry Mode question. Query HTTP directly:

```powershell
$body = @{question='Model 3 如何开启哨兵模式？在家停车时可以自动关闭吗？'} | ConvertTo-Json
$q = Invoke-RestMethod -Method Post -Uri http://localhost:8000/questions -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
Invoke-RestMethod "http://localhost:8000/questions/$($q.id)"
Invoke-RestMethod "http://localhost:8000/jobs/$($q.job_id)"
```

Wait for `answered` and `completed`. The browser polls automatically. Citation
links open `/manual.pdf#page=N`. These are PDF page numbers and can differ from
printed page labels. Page references and images require the remote asset service.

Capture a new full evidence set (creates one record, briefly stops and restarts
the worker; run when no other processing is needed):

```powershell
python scripts/collect_week07_evidence.py --output artifacts/new-week07-evidence
```

This uses only the standard library and Docker CLI. The committed evidence folder
contains the original W07 run, so use a new output directory for later runs.

## Failure and recovery

| Symptom | Check / action |
|---|---|
| Docker pipe missing | Start Docker Desktop; confirm `docker --context default info` |
| RAG unavailable | Check forwarding terminal, AutoDL `/health/ready`, vLLM `/v1/models`, MongoDB ping |
| Address already in use | Check an existing gateway or SSH tunnel before starting another copy |
| Failed question | Restore dependencies, then press Retry or POST `/questions/{id}/retry` |
| Retry returns 409 | Only failed records can be retried; poll current status |
| Job stuck after worker crash | Wait for the lease recovery window (default 300 seconds); inspect worker logs |
| 429 from gateway | Single GPU inference lock is busy; current failed jobs require explicit retry |
| GPU out of memory | Inspect `nvidia-smi`; avoid duplicate CLI, gateway or model processes |
| PDF/image unavailable | Verify remote gateway and `data/Tesla_Manual.pdf` / image data |

Remote logs: `log/qwen3-7b.log`, `log/maie_gateway-w07.log`. Avoid exporting private
configuration or environment dumps while troubleshooting. Logs currently have no
automatic retention configuration. Do not expose the prototype to public users.

## Tests, metrics and backup

Use Python 3.11 with `pip install -e '.[dev]'`. Run `python -m pytest -q tests/unit
tests/integration`, `python -m ruff check .`, and the opt-in live tests described in
the root README. Unit and contract tests use labelled fixtures; live smoke tests
require AutoDL and are separate from model-quality evaluation.

`http://localhost:8000/metrics` and `http://localhost:8100/metrics` expose current
process counters. Optional Prometheus: `docker --context default compose --profile
observability up -d prometheus`. Prometheus was not needed for the captured run.

For a local SQL backup without touching the live volume:

```powershell
docker --context default compose exec -T db pg_dump -U postgres -d maie6000c -f /tmp/manual-backup.sql
docker cp maie6000c-db-1:/tmp/manual-backup.sql .\manual-backup.sql
```

Keep backups private; they may contain user questions. Normal stop:
`docker --context default compose stop`. Stop the SSH forwarding terminal with
Ctrl+C. If using the foreground gateway mode this also stops that gateway. The
background gateway continues until deliberately stopped or the instance shuts down.
Do not use `down -v` for normal shutdown because that deletes the local database volume.
