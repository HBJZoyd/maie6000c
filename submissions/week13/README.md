# Odie W13 final delivery — Real manual Q&A

**Team:** Odie. **Course:** MAIE6000C. **Publisher:** C0216RC / RUICHAO CHEN.
**Product:** Model3 Manual Assistant. **Required tag:** `w13-final`.

## What actually ran

On **28 November2026 at17:59 HKT**, local Docker completed a real Sentry Mode question on an **NVIDIA A100-PCIE-40GB**. A charging question passed a separate live smoke test. Neither answer came from replay or a generated fixture.

| Observed result | Evidence |
|---|---|
| Accepted input and committed pending job before worker | `evidence/live/request-accepted.json`, `database-queued.json` |
| Worker completed a persisted answer | `database-answered.json`, `attempts.json`, `worker-events.jsonl` |
| Actual vLLM model calls and counters | `cloud-events-metrics.txt` |
| Manual references and immutable excerpts | `answer.json`: pages39/115 |
| Restart and idempotency verified | `summary.json` |
| Second real question: charging | `charging-answer.json`: pages142/144; `smoke.xml` |
|59 passing engineering/PostgreSQL tests | `evidence/tests.txt`, `tests.xml` |
|0→6102 vectors→rollback0, exact restored hash | `evidence/index-repair.json` |

Core trace: `728dcdf5-79b7-42ca-94d1-0405e3f963a3`, gateway **5.77s**. Charging trace: `1118e376-ff76-42fd-84e0-2ec6d6c71cea`, gateway3.94s. These include retrieval/generation and are not latency benchmarks or accuracy scores.

## Review order

1. [Technical brief](final-technical-brief.md).
2. [PPT](Odie_W13_Final_Demo.pptx) and [speaker script](SPEAKER_SCRIPT.md).
3. [Demo runbook](DEMO_RUNBOOK.md), [evaluation](EVALUATION.md), [rubric map](RUBRIC_MAP.md).
4. [Architecture](../../docs/architecture.md), [operations](../../docs/operations.md), [ADRs](../../docs/adrs/).
5. [Artifact manifest](ARTIFACT_MANIFEST.json) and [submission handoff](SUBMISSION.md).

## What changed

All1571 migrated files (43,425,756,317 bytes) matched source hashes before repair. The empty vector index became6102 genuine vectors. Target adapters corrected the Milvus `.db` URI and the text schema: measured maximum5657 UTF8 bytes, stored limit8192, dynamically read by the gateway. Original source `infer.py` and `src/` were not edited.

At the user’s request, the old simulated HTML, original offline/replay run evidence, Compose configurations and explicitly labelled adapters are retained. [Historical reports, PPT and script](history/simulated-final/README.md) are exact copies from the existing final commit. They are separate from the new real A100 evidence. W07 history and all existing commits/tags are preserved.

## Honest readiness

Real model-backed engineering acceptance, persistence and restart have passed. This is still single-manual/local access; human-labelled factual accuracy, broader load testing and public authorization are incomplete. Private weights/full manual are not distributed. GPU power-off after delivery is intentional; a later live demonstration requires an authorized GPU, assets and tunnel.
