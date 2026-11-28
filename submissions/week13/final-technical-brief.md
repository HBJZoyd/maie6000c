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
