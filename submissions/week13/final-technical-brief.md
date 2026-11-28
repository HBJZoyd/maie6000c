# Final technical brief

## Problem and scope

Model3 owners and support staff need to locate instructions in a long Chinese manual and inspect an answer's support. The application accepts single-turn questions, persists input before background work, saves cited answers and retains history. It does not control vehicles, select across model years, authenticate public users or replace the actual manual. MAIE6000C is the course; Odie is the team.

## Integrated implementation

FastAPI atomically commits question and pending job before HTTP202. An independent worker claims it, records an attempt and calls the AI service. Authenticated localhost SSH forwarding reaches the GPU RAG gateway. The pipeline retains existing BM25 and BGE-M3 dense/sparse retrieval, trained reranking and fine-tuned4-bit Qwen3 via vLLM. Generated steps must reference actual retrieved IDs; gateway and application validate manual identity, page bounds, excerpt checksums and the complete envelope before saving.

ZHANG Yiming's reliability layer is preserved. Idempotency protects duplicate acceptance. Claim tokens, generations, heartbeats and token-checked completion fence stale owners; retries are bounded and attempts remain inspectable. This is at-least-once inference: crashes may repeat GPU work even when fenced writes protect stored state.

## Executed migration and repair

The user approved an A10040GB backup and explicitly selected A100 as the target. These results make no A800 inference claim. The private system image preserved Python3.12.13 and original GPU packages; data moved separately. Platform copying required an explicitly authorized temporary source stop, followed by no-GPU restoration.

All **1571 files /43,425,756,317 bytes** matched SHA256 before repair. The original Milvus collection was empty. A separate copy of genuine Mongo data exported **6102 documents**; the original embedding/retriever built6102 vectors. The measured maximum was **5657 UTF8 bytes**, requiring text length **8192**, not legacy512.

Two concrete incompatibilities were corrected in adapters: pymilvus rejected a `.sqlite` staging URI but accepted `.db`; the original retriever also passed a512 schema while opening an8192 release. The gateway now reads the stored field before constructing that retriever. Original source `infer.py` and `src/` stayed unchanged.

The native transaction retained baseline, changed database, reconstructing binary patch, literal command/output ledger and executable rollback. Matching COUNT inputs observed **0 /6102 /0** for baseline, modified and restored copies. Restored SHA256 equalled baseline; the patch reconstructed the modified hash. Only then was the repaired release deployed. A writable runtime Milvus copy remains separate from that release, and managed Mongo uses `runtime/mongo`.

## Real validation

At2026-11-28 17:59 HKT, question `728dcdf5-79b7-42ca-94d1-0405e3f963a3` asked about Sentry enabling and home exclusion. With the worker paused, SQL already held queued input/pending job and no answer. After resumption, Qwen3 was actually called; the saved result cited manual pages39/115 with excerpts and model/index/prompt identity. Idempotent resubmission returned the same request; local-stack restart retained the same answer and attempts. The collector exited0.

A separate charging question passed live smoke and persisted pages142/144. Gateway durations were5.77s and3.94s, including retrieval and generation. The corresponding cloud snapshot shows two chat-completion HTTP200 responses,2 successful requests,5793 prompt tokens and641 generated tokens. These corroborate model execution, not broad quality/throughput.

For the current real-path implementation, **59 unit/integration/PostgreSQL tests** passed with two dependency deprecation warnings. The additional real-GPU smoke passed; Ruff, JavaScript syntax and PowerShell parsing passed. Historical simulated runs remain explicitly labelled and isolated from the real deployment.

## Findings and limitations

The engineering acceptance event is real with authorized private assets. Citation integrity is not semantic entailment. The generated Sentry first instruction omits a UI-icon detail and still requires human checking against context. One manual and two distinct live questions cannot support generalized accuracy, safety or capacity claims. Human-reviewed evaluation, multi-manual/version selection, public authorization and controlled load/failure experiments remain next priorities.

The delivery preserves W03/W04/W07, ZHANG Yiming’s reliability contribution and the existing final commit. The old recorded demo is retained alongside dated live evidence; neither is relabelled as the other. GPU resources are temporary: platform power-off after engineering stops charges without releasing data. A new live demonstration requires restarting the GPU, environment and tunnel.

## Clean-start and operational hardening

The existing A100 was restarted, authorized release checks passed and the actual model/gateway reached readiness. New local source commit `6e885e9cc156789d23ebf1966b128a89d76859d1` was cloned with `--no-local` into an unused directory. The initial checkout was clean, `.env` absent and a separate PostgreSQL database contained zero questions. Configuration came from `.env.example`, not the development configuration. Isolated host ports were 18000/18100/15432.

At 21:49 HKT, trace `4f9fe954-2922-4b5e-9994-5cbf0d08bdfd` completed actual generation, queued SQL before worker execution, valid citations, saved answer, idempotency and restart retention. Its gateway duration was 5.39 s; the restarted vLLM snapshot showed one successful request, 2537 prompt tokens and 265 generated tokens. Those counters are a separate process lifetime from the initial two-request snapshot and must not be conflated. The temporary verification stack stopped without deleting its named volume.

The Remote launcher now checks API/database/RAG ready and live mode and fails closed otherwise. Explicit API ports are passed to Compose and the readiness URL. Four PowerShell contracts with explicit Docker/HTTP test doubles cover unavailable, fixture, live and configuration-only behavior. A native baseline/change/rollback probe observes false acceptance exit0, refusal exit1 and original false acceptance exit0, with exact restored hash. This is a launcher regression proof, not model evidence.

The clean-start script records exact source and initial state and refuses an existing checkout, occupied ports, reused project or nonempty question history. The connection helper supports existing identity/known-host files, managed services and tunnel-only reconnection. The operations guide defines prerequisites, asset entitlement/hash checks, safe host verification, startup deadlines, diagnosis, rollback boundaries and non-destructive cleanup. Publisher for these improvements is HBJZoyd; previous authorship is unchanged.

Reproduction is conditional on an authorized pre-provisioned GPU environment. The pending-release source was local Git, not a remote clone; Docker caches are permitted and no independent second-operator claim is made. Factual correctness and load capacity remain outside these checks.

## Released-repository reproduction

After HBJZoyd published the improvements, the public GitHub repository was cloned at `feb29e5d833345f283c35195a70e7f57f33e65d6` into a second new directory. No old configuration or local database was copied. A new project/database and ports 18001/18101/15433 started with zero questions. At 21:57–21:58 HKT, trace `9d80b78f-b158-40b4-9671-92e12538957e` completed the same real acceptance sequence and restart retention, gateway 3.34 s, collector exit0, non-destructive cleanup exit0.

A real idle-forward interruption also changed RAG readiness to unavailable and then back to ready/live without disturbing API/database readiness. This is a dependency-readiness drill, not an in-flight worker fault experiment. Both clean deployments used the same operator and an authorized existing GPU environment. Private-asset availability remains explicit. The final evidence/material update does not change the tested application/runtime code.
