# W13 speaker script — real A100 delivery and clean-start reproduction

Team Odie; MAIE6000C. Latest publisher: HBJZoyd. Branch: w13. Required tag: w13-final.
Historical authorship and simulated materials are retained; this technical presentation is not limited to the old short pitch.

## Slide 1: Model 3 Manual Assistant

We are Team Odie, presenting our MAIE6000C final project. MAIE6000C is the course, not the product. The application helps Model 3 owners and support staff ask questions about one Chinese owner manual, inspect the cited passages and return to saved history. Today’s evidence is a real A100 model-backed run on 28 November 2026. It is not the previous recorded demonstration. We will follow one submitted question through storage, a separate worker, actual inference and a saved answer, then distinguish what that proves from what still requires human evaluation.

中文彩排提示：我们是 Odie，小组产品是车书问答助手，MAIE6000C 是课程。展示的是 11 月 28 日 A100 真实推理，不是旧模拟回放。重点讲清完整系统链路及边界。

Sources: submissions/week13/README.md; evidence/live/summary.json

## Slide 2: The integrated system path

The browser sends a question to FastAPI. One PostgreSQL transaction writes both the question and pending job before the API returns HTTP 202. A separate worker claims that job and records an attempt. It calls the AI service, which reaches the GPU gateway through an authenticated localhost SSH tunnel. Retrieval, reranking and Qwen3 generation execute there. The evidence envelope is validated before the worker saves the answer. The browser reads that persisted result and its source references. If a dependency is unavailable, the system reports that state instead of substituting a fake answer.

中文彩排提示：问题先入库再返回 202，worker 独立领取任务，经 AI 服务和 SSH 隧道调用 GPU。真实检索、重排和模型生成后，校验引用并保存结果。依赖不可用时不使用模拟答案。

Sources: docs/architecture.md; services/api/app/main.py; services/worker/app/main.py; scripts/rag_gateway.py

## Slide 3: Migration and recoverable index repair

The user selected an A100 40GB backup as the working target, so every compute result here refers to A100 rather than A800. The existing system image preserved the GPU environment; the data moved separately. All 1571 files, totalling 43.43 GB, matched their source SHA256 before target repair. The original vector collection was empty. A copy of genuine Mongo data supplied 6102 documents for rebuilding with the original embedding and retriever. We tested the pristine, changed and rolled-back databases with the same count query. Rollback recovered zero rows and the exact original hash before the repaired index was deployed.

中文彩排提示：只汇报实际 A100 结果。全量 1571 文件哈希通过后，从真实 Mongo 文档重建 6102 条向量。基线、修改、回滚用同一查询验证，哈希恢复一致后才部署。

Sources: evidence/index-repair.json; evidence/validation.json; scripts/rebuild_target_index.py

## Slide 4: A real Sentry Mode question

The core question asked how to enable Sentry Mode and exclude the home location. The collector paused the worker so we could observe queued SQL input with no answer. After resuming the worker, the gateway made an actual Qwen3 chat-completion request and saved an answered result with manual pages 39 and 115. The gateway logged 5.77 seconds including retrieval and generation. Reusing the submission key returned the same request. A whole local-stack restart preserved its answer and attempts. The trace ID and raw engineering evidence are in the report. This is proof of execution and persistence, not a factual accuracy score.

中文彩排提示：展示哨兵模式与住宅除外真实问题。SQL 排队后启动 worker，真实模型回答带 39、115 页引用。5.77 秒是网关总耗时；幂等和重启保留结果均通过，但不等于准确率。

Sources: evidence/live/request-accepted.json; database-queued.json; answer.json; summary.json; worker-events.jsonl

## Slide 5: AI function and source integrity

The AI contribution is grounded generation, not a keyword lookup. The original pipeline combines BM25 with BGE-M3 dense and sparse retrieval, applies the existing trained reranker and calls the fine-tuned four-bit Qwen3 model through vLLM. The response must cite IDs from the candidate packet. Manual identity, page bounds and excerpt hashes are checked again at the application boundary. The repaired Milvus field was 8192 bytes, so the adapter now reads that stored schema rather than passing the legacy 512 default. That change lets the unchanged original retriever open the real rebuilt index.

中文彩排提示：AI 是基于真实检索证据的生成，不是关键词模拟。保留 BM25、稠密/稀疏检索、原重排器和 Qwen3。适配器读取真实索引字段长度，引用完整性双重校验，不改源核心代码。

Sources: scripts/rag_gateway.py; scripts/rag_evidence.py; services/common/schemas.py; evidence/live/answer.json

## Slide 6: Verification and operational evidence

With historical simulation modes retained separately, 59 unit, integration and real PostgreSQL tests passed. They exercise reliability and evidence handling, not model accuracy. A separate opt-in live GPU smoke test asked about charging limits and scheduling and saved references to pages 142 and 144. Its gateway duration was 3.94 seconds. The dated cloud snapshot shows two successful model requests, 5793 prompt tokens and 641 generated tokens. These logs and counters corroborate actual generation. We keep them separate from API health, database persistence and the two dependency deprecation warnings reported by the deterministic suite.

中文彩排提示：59 项工程与真实 PostgreSQL 测试通过；另跑充电问题的真实 GPU smoke，通过并引用 142、144 页。日志和请求/token计数证明模型执行，但两个样本不能做性能或准确率基准。

Sources: evidence/tests.txt; tests.xml; evidence/live/smoke.xml; charging-answer.json; cloud-events-metrics.txt

Update: four isolated PowerShell contracts reject unavailable/fixture backends, accept live readiness and distinguish configuration-only checks. They are explicitly test-double checks, not inference. A separate clean checkout and empty database also completed a new real inference and local-stack restart; see evidence/clean-start/.

## Slide 7: Clean startup and working demo

We restarted the existing authorized A100 and verified its release assets. Then we cloned source commit 6e885e9cc156789d23ebf1966b128a89d76859d1 into a new directory without local hardlinks. Git status was clean, no .env existed and the new PostgreSQL database initially held zero questions. The launcher generated configuration, built isolated containers and required actual ready/live status. A new question passed HTTP202, queued SQL before worker execution, a real A100 model call, cited persistence, idempotency and a whole local-stack restart. The trace is 4f9fe954-2922-4b5e-9994-5cbf0d08bdfd. The script then stopped only the verification project without deleting its named volume. This establishes fresh local application/database reproduction against a provisioned private GPU, not redistribution or cold recreation of the private model environment.

中文彩排提示：新 Git 检出、无旧环境文件、独立空数据库，再跑真实模型并验证重启保留。不是把旧开发数据库或回放答案复制过来；GPU 私有资产仍是明确前提。

Sources: docs/reproducibility.md; evidence/clean-start/reproduction.json; evidence/clean-start/summary.json; scripts/verify-clean-start.ps1

Published GitHub clone update: source feb29e5d833345f283c35195a70e7f57f33e65d6, fresh empty database and new trace 9d80b78f-b158-40b4-9671-92e12538957e passed the same real inference, queued SQL, idempotency and restart checks at 21:57–21:58 HKT. Collector and non-destructive cleanup exited0. A separate idle SSH-forward drill changed readiness to unavailable and restored live readiness; it did not interrupt an in-flight job. See evidence/remote-clean-start/. Both clean runs used the same operator and pre-provisioned authorized GPU assets.

## Slide 8: Delivery and remaining limits

The latest improvements are published by HBJZoyd on branch w13 with required tag w13-final. Earlier simulated final d85b720 is preserved as w13-1, previous real result 6fbec03 as w13-2, and ZHANG Yiming's unchanged reliability commit b6c5ef3 as w13-reliability. No prior commits or simulated materials are deleted. Startup and operations documentation now describe asset entitlement, verified SSH, actual readiness, failure handling, safe cleanup and the clean-clone procedure. One Chinese manual, local access, no completed human-labelled accuracy benchmark and no controlled capacity study remain honest limits. A new live demonstration requires starting the GPU and authenticated forwarding; do not substitute a recording. The Canvas handoff must use the verified full peeled tag SHA, and the team performs the official Canvas submission.

中文彩排提示：最新发布者为 HBJZoyd；最新分支 w13，标签 w13-final。旧模拟、上一版真实成果和张一鸣优化成果都有独立保留引用。运维和启动证据已补齐，但不承诺准确率、容量或评分。

Sources: SUBMISSION.md; EVALUATION.md; docs/operations.md; evidence/clean-start/reproduction.json

## Live presentation checklist

1. Show ready/live, then enter a new question.
2. Show queued SQL, worker attempt, actual model event and stored answer.
3. Open cited manual/excerpts and correlate logs/metrics.
4. Explain restart retention and reproduce the clean-clone command.
5. State private GPU prerequisites and unmeasured factual accuracy.
6. Retain old simulations as labelled history, never substitute them silently.
