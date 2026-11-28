# W13 speaker script — real A100 delivery

Team Odie; MAIE6000C final project. Publisher: C0216RC / RUICHAO CHEN.
The script supports a technical presentation plus the working-system demonstration; no old 1.5-minute pitch limit is assumed.

## Slide 1: Model 3 Manual Assistant

We are Team Odie, presenting our MAIE6000C final project. MAIE6000C is the course, not the product. The application helps Model 3 owners and support staff ask questions about one Chinese owner manual, inspect the cited passages and return to saved history. Today’s evidence is a real A100 model-backed run on 28 November 2026. It is not the previous recorded demonstration. We will follow one submitted question through storage, a separate worker, actual inference and a saved answer, then distinguish what that proves from what still requires human evaluation.

中文彩排提示：我们是 Odie，小组产品是车书问答助手，MAIE6000C 是课程。展示的是 11 月 28 日 A100 真实推理，不是旧模拟回放。重点讲清完整系统链路及边界。

## Slide 2: The integrated system path

The browser sends a question to FastAPI. One PostgreSQL transaction writes both the question and pending job before the API returns HTTP 202. A separate worker claims that job and records an attempt. It calls the AI service, which reaches the GPU gateway through an authenticated localhost SSH tunnel. Retrieval, reranking and Qwen3 generation execute there. The evidence envelope is validated before the worker saves the answer. The browser reads that persisted result and its source references. If a dependency is unavailable, the system reports that state instead of substituting a fake answer.

中文彩排提示：问题先入库再返回 202，worker 独立领取任务，经 AI 服务和 SSH 隧道调用 GPU。真实检索、重排和模型生成后，校验引用并保存结果。依赖不可用时不使用模拟答案。

## Slide 3: Migration and recoverable index repair

The user selected an A100 40GB backup as the working target, so every compute result here refers to A100 rather than A800. The existing system image preserved the GPU environment; the data moved separately. All 1571 files, totalling 43.43 GB, matched their source SHA256 before target repair. The original vector collection was empty. A copy of genuine Mongo data supplied 6102 documents for rebuilding with the original embedding and retriever. We tested the pristine, changed and rolled-back databases with the same count query. Rollback recovered zero rows and the exact original hash before the repaired index was deployed.

中文彩排提示：只汇报实际 A100 结果。全量 1571 文件哈希通过后，从真实 Mongo 文档重建 6102 条向量。基线、修改、回滚用同一查询验证，哈希恢复一致后才部署。

## Slide 4: A real Sentry Mode question

The core question asked how to enable Sentry Mode and exclude the home location. The collector paused the worker so we could observe queued SQL input with no answer. After resuming the worker, the gateway made an actual Qwen3 chat-completion request and saved an answered result with manual pages 39 and 115. The gateway logged 5.77 seconds including retrieval and generation. Reusing the submission key returned the same request. A whole local-stack restart preserved its answer and attempts. The trace ID and raw engineering evidence are in the report. This is proof of execution and persistence, not a factual accuracy score.

中文彩排提示：展示哨兵模式与住宅除外真实问题。SQL 排队后启动 worker，真实模型回答带 39、115 页引用。5.77 秒是网关总耗时；幂等和重启保留结果均通过，但不等于准确率。

## Slide 5: AI function and source integrity

The AI contribution is grounded generation, not a keyword lookup. The original pipeline combines BM25 with BGE-M3 dense and sparse retrieval, applies the existing trained reranker and calls the fine-tuned four-bit Qwen3 model through vLLM. The response must cite IDs from the candidate packet. Manual identity, page bounds and excerpt hashes are checked again at the application boundary. The repaired Milvus field was 8192 bytes, so the adapter now reads that stored schema rather than passing the legacy 512 default. That change lets the unchanged original retriever open the real rebuilt index.

中文彩排提示：AI 是基于真实检索证据的生成，不是关键词模拟。保留 BM25、稠密/稀疏检索、原重排器和 Qwen3。适配器读取真实索引字段长度，引用完整性双重校验，不改源核心代码。

## Slide 6: Verification and operational evidence

With historical simulation modes retained separately, 59 unit, integration and real PostgreSQL tests passed. They exercise reliability and evidence handling, not model accuracy. A separate opt-in live GPU smoke test asked about charging limits and scheduling and saved references to pages 142 and 144. Its gateway duration was 3.94 seconds. The dated cloud snapshot shows two successful model requests, 5793 prompt tokens and 641 generated tokens. These logs and counters corroborate actual generation. We keep them separate from API health, database persistence and the two dependency deprecation warnings reported by the deterministic suite.

中文彩排提示：59 项工程与真实 PostgreSQL 测试通过；另跑充电问题的真实 GPU smoke，通过并引用 142、144 页。日志和请求/token计数证明模型执行，但两个样本不能做性能或准确率基准。

## Slide 7: Working-system demonstration

For a new live demonstration we first start the authorized GPU and tunnel, then verify that system status says RAG ready and mode live. In the browser we submit a question, inspect its processing history and expand the cited excerpts. We correlate the request with worker events and cloud completion logs, and open the hash-checked manual. The formal collector can pause the worker and restart the local stack to reproduce the persistence checks. If the tunnel or model is unavailable, we show that state and restore the dependency. We do not replace it with the old recording. After engineering is finished, temporary access is removed and the GPU is powered off through the platform.

中文彩排提示：先检查真实 readiness，再提交、看尝试记录、展开引用并核对手册。日志与指标关联请求。故障时诚实展示不可用，不切换旧回放；工程完成后清理临时访问并由平台关机。

## Slide 8: Delivery and remaining limits

The final delivery preserves the semester milestones, ZHANG Yiming’s reliability contribution and the existing final commit. The existing final commit and its simulated materials are preserved alongside the new real report, slides, script, runbook and dated live evidence. The new real-results commit is appended without deleting earlier commits; the publishing identity and checkpoint names remain unchanged. Our limits remain important: one Chinese manual, local access and no completed human-labelled factual benchmark. Valid citations alone do not establish that every instruction is supported; the first generated Sentry instruction omits a UI-icon detail and needs human review. We should next evaluate factual support with independent reviewers, then add manual-version selection and public authorization before expanding deployment. The report is the primary review artifact; the Canvas handoff must use the verified full peeled commit SHA.

中文彩排提示：保留学期里程碑、张一鸣的优化及旧期末提交，旧模拟材料保留，新材料对应真实结果。局限是单手册、本地访问及未完成事实基准，引用有效不等于语义正确。下一步先做人工事实评估，再做版本和访问控制。

## Review questions

- Did this make actual model calls? Yes: dated cloud chat-completion HTTP200 events and changing token counters accompany saved live results.
- Is a valid page an accuracy score? No; semantic support and vehicle-safety qualifications need human review.
- Is inference exactly once? No; at-least-once GPU work is combined with fenced database writes.
- Why does a later demo need setup? Authorized weights/manual are private and the GPU is temporary, not permanent hosting.
- What is preserved? W07 history/tag, ZHANG Yiming’s contribution and the existing final commit; simulated materials are retained beside real results.
