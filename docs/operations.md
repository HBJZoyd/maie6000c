# Operations

## GPU assets and startup

Use authorized copies of the manual, model weights, embeddings, reranker, BM25 data, Mongo snapshot and rebuilt Milvus index. The verified target was A10040GB; there is no A800 execution claim. Keep its original Python3.12 environment and pinned packages. Git excludes private assets, credentials and databases.

Deploy the five adapters beside the RAG root without replacing original `infer.py` or `src/`: `rag_gateway.py`, `rag_evidence.py`, `rag_assets.py`, `rag_store.py`, `start_rag.py`.

```bash
export PYTHONDONTWRITEBYTECODE=1 MONGO_HOST=127.0.0.1
python rag_assets.py capture --root RAG_ROOT --manual-version ACTUAL_MANUAL_VERSION
python start_rag.py --root RAG_ROOT --check-assets-only
python start_rag.py --root RAG_ROOT --manage-services --mongod MONGOD_PATH
```

The verified manual is255 pages, version `sha256-baaf110b1b70cdf6`, PDF SHA256 `baaf110b1b70cdf6f2493e071ed5ac3248bed732635ba74f77ae376dae659716`. Capture only quiescent release assets. For an original empty index, `scripts/rebuild_target_index.py` retains baseline, patch, literal ledger and executable rollback; it deliberately refuses a nonempty baseline. Do not casually rerun it against a live release.

The supervisor restores only an empty managed Mongo collection from `data/manual_text.jsonl`, checks CUDA, starts absent dependencies and waits for real readiness. Mongo/vLLM bind loopback; the gateway defaults to127.0.0.1:6001. Logs are under `runtime/`. The observed vLLM memory fraction was0.55; this is configuration, not a capacity benchmark.

## Local application

Create `.env` from `.env.example` only if absent. Keep credentials outside Git. Establish an authorized localhost SSH tunnel, then run `scripts/start.cmd -Mode Remote`. It drains old workers before additive migrations and preserves database volumes. Check `/system/status`, not just a responsive home page.

```powershell
docker --context default compose -p maie6000c -f compose.yaml ps
docker --context default compose -p maie6000c -f compose.yaml logs --tail 80 worker
```

Inspect `/questions/ID/attempts`, `/jobs/ID`, `/metrics`, cloud `runtime/rag.log` and `runtime/llm.log`. Chat-completion HTTP200 plus generated-token/request counters corroborate model execution. Gateway duration is not isolated model latency.

## Troubleshooting

- API/database ready but RAG unavailable: check forwarding and GPU Mongo/model/gateway logs.
- Milvus URI rejected: use the supported `.db` suffix.
- Schema mismatch: match stored text length, not legacy512. The adapter now reads it dynamically.
- Invalid evidence: retain attempts and inspect IDs/pages/manual identity; never substitute a synthetic answer.
- Timeout/tunnel loss: restore dependencies before manually retrying the saved question; automatic retries are bounded.

## Shutdown

Do not set automatic timers. After engineering, remove temporary authorized keys, stop local forwarding and use platform **power off**, verifying stopped status. OS shutdown alone is not a billing check. Do not release instances/data disks. Local `compose down` preserves volumes; never use `down -v` for normal stop. A later demonstration needs the authorized GPU and tunnel restarted.
