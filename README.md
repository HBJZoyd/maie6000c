# Model 3 Manual Assistant — Team Odie

MAIE6000C is the course; the product is a vehicle-manual Q&A application. W03/W04/W07 milestones and ZHANG Yiming's reliability upgrade are preserved.

## Verified final delivery

On **28 November 2026**, local FastAPI, PostgreSQL, a separate worker and an AutoDL **A100 40GB** completed real Qwen3-backed questions. This is not a response replay or synthetic demonstration.

- HTTP202 follows committed question/job records.
- BM25 and Milvus dense/sparse retrieval, existing reranking and Qwen3 generation produce cited answers.
- Saved envelopes retain page links, excerpts/checksums and model/index/prompt identities.
- Queued SQL, completed attempts, idempotency, metrics and restart survival were captured.
- 59 unit/integration/PostgreSQL tests and one additional real-GPU smoke test passed.
- The Remote launcher now fails closed unless API/database/RAG are ready in live mode; four isolated PowerShell startup contracts cover unavailable/fixture/live/configuration-only behavior.

Start at [the final report and evidence index](submissions/week13/README.md).

## Run the real application

Prerequisites: Docker Desktop, authorized GPU assets/environment, MongoDB, a ready RAG gateway and an authenticated SSH tunnel. Weights and the complete manual are deliberately excluded from Git.

```powershell
ssh -N -L 127.0.0.1:6001:127.0.0.1:6001 -p SSH_PORT root@SSH_HOST
# In another terminal, from the checkout:
scripts\start.cmd -Mode Remote
```

Open `http://localhost:8000/app`. `/system/status` must report `rag=ready` and `mode=live`; otherwise new questions stay disabled. Existing history remains readable. The default gateway URL is `http://host.docker.internal:6001`. See [operations](docs/operations.md) and [clean-start reproduction](docs/reproducibility.md). This is a dated live validation, not a permanently hosted service. GPU power-off after delivery avoids ongoing charges; a later live demo requires restarting the authorized GPU and tunnel.

## Verify

```powershell
docker --context default compose -p odie-verification -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker --context default compose -p odie-verification -f compose.test.yaml down
python scripts/collect_final_evidence.py --mode live --base-url http://127.0.0.1:8000 --project maie6000c --compose-file compose.yaml --pause-worker --restart --timeout 900
```

The real launcher defaults to Remote mode. Historical fixture/replay modes remain explicitly labelled in separate odie-offline and odie-demo projects; they never silently replace the real model. See [the preserved simulation archive](submissions/week13/history/simulated-final/README.md). Normal shutdown never uses `down -v`.

## Boundaries

One Chinese manual, single-turn questions and local access. Citation validity is not factual accuracy or a vehicle-safety guarantee. Human semantic review, multi-manual selection, public authorization and broader load testing remain future work.

## Clean checkout validation

A new clone of the published GitHub source and a new empty PostgreSQL database completed actual A100 inference, queued persistence, worker processing, citations, idempotency and restart. The [executed remote-clone proof](submissions/week13/evidence/remote-clean-start/reproduction.json) records the exact tested source. This is conditional on authorized private GPU assets, not a weight-free offline inference claim.

## Release references

Latest maintained branch: `w13`; required tag: `w13-final`; latest publisher: HBJZoyd. `w13-1` retains the old simulated final, `w13-2` the previous real final, and `w13-reliability` ZHANG Yiming's unchanged optimization. Prior authorship and materials remain intact.
