# Odie W13 final delivery — Real manual Q&A

**Team:** Odie. **Course:** MAIE6000C. **Latest publisher:** HBJZoyd.
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

## Released GitHub clone verified

A second reproduction cloned **https://github.com/HBJZoyd/maie6000c.git** at `feb29e5d833345f283c35195a70e7f57f33e65d6`, using a second unused directory/project/database and ports 18001/18101/15433. At **21:57–21:58 HKT**, its initial database again held **0 questions**; new trace `9d80b78f-b158-40b4-9671-92e12538957e` passed real A100 generation (gateway **3.34 s**), queued SQL, citations, persistence, idempotency and restart. Cleanup exited0 without deleting the named volume. See [remote-clone proof](evidence/remote-clean-start/reproduction.json).

A separate idle readiness drill observed live ready → RAG unavailable when forwarding stopped → live ready after restoration, while API/database stayed ready. It did not interrupt an in-flight job. Both runs used the authorized GPU dependency and the same operator; neither is an independent second-person or accuracy benchmark. Final evidence-only updates leave the tested runtime code unchanged.

## First clean-start acceptance and operations update

At 21:49 HKT on 28 November 2026, source `6e885e9cc156789d23ebf1966b128a89d76859d1` was cloned from a local Git object source with `--no-local` into a new directory. The checkout was clean, `.env` absent, configuration generated from the example and the isolated PostgreSQL database initially held **0 questions**. Fresh request `4f9fe954-2922-4b5e-9994-5cbf0d08bdfd` completed real A100 inference (gateway 5.39 s), queued SQL, cited persistence, idempotency and whole-local-stack restart. The verification project was then stopped without deleting its named volume.

This pending-release test is **not** described as a remote clone or an independent second-person review. It reuses the authorized GPU assets, not the old local database or saved answer. The exact scope is recorded in [clean-start evidence](evidence/clean-start/reproduction.json) and [reproduction instructions](../../docs/reproducibility.md).

The Remote launcher now refuses unavailable or fixture readiness instead of reporting success merely because containers run. Four isolated PowerShell contracts cover unavailable/fixture/live/configuration-only states, separately from the 59 Python tests and live inference. [Operations](../../docs/operations.md) now specifies host verification, private-asset prerequisites, managed service startup, readiness, diagnosis, retention and cleanup.

Latest release branch: `w13`; required tag: `w13-final`. Historical references: `w13-1` (old simulated final), `w13-2` (previous real final), `w13-reliability` (unchanged ZHANG Yiming optimization). Earlier authorship and all simulated materials remain intact.

## Review order

1. [Technical brief](final-technical-brief.md).
2. [PPT](Odie_W13_Final_Demo.pptx) and [speaker script](SPEAKER_SCRIPT.md).
3. [Demo runbook](DEMO_RUNBOOK.md), [evaluation](EVALUATION.md), [rubric map](RUBRIC_MAP.md).
4. [Architecture](../../docs/architecture.md), [operations](../../docs/operations.md), [ADRs](../../docs/adrs/).
5. [Artifact manifest](ARTIFACT_MANIFEST.json) and [submission handoff](SUBMISSION.md).

## What changed

All1571 migrated files (43,425,756,317 bytes) matched source hashes before repair. The empty vector index became6102 genuine vectors. Target adapters corrected the Milvus `.db` URI and the text schema: measured maximum5657 UTF8 bytes, stored limit8192, dynamically read by the gateway. Original source `infer.py` and `src/` were not edited.

At the user’s request, the old simulated HTML, original offline/replay run evidence, Compose configurations and explicitly labelled adapters are retained. [Historical reports, PPT and script](history/simulated-final/README.md) are exact copies from the existing final commit. They are separate from the new real A100 evidence. W07 history/tag and all existing commits are preserved; the required final release tag advances to the verified latest delivery.

## Honest readiness

Real model-backed engineering acceptance, persistence and restart have passed. This is still single-manual/local access; human-labelled factual accuracy, broader load testing and public authorization are incomplete. Private weights/full manual are not distributed. GPU power-off after delivery is intentional; a later live demonstration requires an authorized GPU, assets and tunnel.
