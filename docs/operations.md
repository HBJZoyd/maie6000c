# Operations

Team Odie. See [the detailed current runbook](reliability-upgrade.md) for startup,
task ownership, evidence contracts and pending GPU verification.

## No-AutoDL engineering deployment

Start Docker Desktop, open CMD in the repository and run:

~~~cmd
scripts\start.cmd
~~~

Open http://localhost:8020/app. This deployment uses synthetic, visibly labelled
answers and its own project/volumes. Initial builds need internet. It does not
validate real AI. Existing .env, real deployment data and W07 tags are preserved.

~~~cmd
docker --context default compose -p odie-offline -f compose.offline.yaml ps
docker --context default compose -p odie-offline -f compose.offline.yaml logs --tail 80 worker
docker --context default compose -p odie-offline -f compose.offline.yaml stop
~~~

Start again using the wrapper. Normal stop retains volumes. Never delete volumes
when you intend to preserve question history.

## Real backend

Provision trusted private assets and the Python 3.12 GPU environment as described
in the detailed runbook. Capture the actual manual version and asset hashes,
export MongoDB records and preserve an immutable release. The source requirements
snapshot exists; fresh GPU installation/CUDA compatibility remain unverified.

start_rag.py checks assets/runtime, verifies CUDA and can supervise MongoDB,
vLLM and the gateway. It restores records only into an empty collection and stops
only its own child processes. Dependencies must be ready, not merely running.
Remote logs are under RAG/runtime/. Real gateways bind to loopback.

The updated connect-rag.ps1 copies all required adapter modules and maintains
forwarding once assets are prepared. Its foreground process must remain open.
The new gateway requires an asset manifest; uploading one old file is insufficient.
W07 private configuration can describe existing dependencies but is not the new
deployment procedure.

After the backend/tunnel is ready:

~~~cmd
scripts\start.cmd -Mode Remote
~~~

This uses the existing maie6000c project and configured ports. A v1 gateway is
reported unavailable for new answers. Existing W07 text/excerpts remain readable.

## Inspect and troubleshoot

/system/status reports backend availability and live/fixture mode. /health/live
checks process liveness; API /health/ready checks SQL (503 on failure).
Gateway readiness checks MongoDB and the expected LLM model, with a short cache.
It is not a quality score.

Inspect /questions/{id}, /jobs/{job_id} and /questions/{id}/attempts.
Logs carry job/attempt IDs. Transient retries remain queued until scheduled;
invalid evidence fails immediately. Manual retry preserves attempt history.

| Symptom | Action |
|---|---|
| Docker engine missing | Start Docker Desktop and wait for its Linux engine |
| Backend unavailable | Check tunnel, asset/runtime validation, MongoDB and expected LLM |
| 429 / busy | Inspect scheduled retry; automatic attempts are bounded |
| Task stuck after crash | Inspect heartbeat/lease; recovery fences old ownership |
| Invalid evidence | Inspect safe error code and matching gateway contract/release |
| PDF conflict (409) | Retain the cited manual version; do not substitute newer pages |
| GPU out of memory | Check duplicate processes; measure before raising concurrency |

Credentials stay in private configuration. Do not export environment dumps or
commit weights, manuals, indexes, database directories or passwords.
The API remains a local single-user prototype without public authentication.

## Verification

~~~cmd
docker --context default compose -p odie-verification -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker --context default compose -p odie-verification -f compose.test.yaml down
python scripts\verify_offline.py --restart
~~~

The test project has no database host port and uses temporary PostgreSQL schemas.
The verifier requires fixture mode, saves its own test question and checks SQL,
PDF identity and restart persistence. Its output states real AI was not invoked.

Before final real-AI readiness claims, run real smoke tests, evaluate labelled
questions, and rehearse GPU startup from a fresh environment. W07 real evidence
remains historical. Keep operational logs and backups private.
