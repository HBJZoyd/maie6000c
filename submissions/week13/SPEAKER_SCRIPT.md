# W13 Speaker Script

Team Odie. Presenter/submission account: C0216RC / RUICHAO CHEN.
Suggested speech: four to five minutes plus the system demonstration. The supplied final assignment sets no speech duration.

## Slide 1: Model 3 Manual Assistant

We are team Odie. Our project helps Model 3 owners and support staff ask questions about a Chinese owner manual and inspect the sources behind an answer. We developed a complete application path around that AI function: submit a question, persist it, process it in a separate worker and save the result. Our presentation uses a dated Sentry Mode recording at the AI boundary. The API, PostgreSQL and worker execute normally, so we can demonstrate the engineering path repeatedly.

中文彩排提示：我们是 Odie 小组。项目帮助车主和支持人员查询中文手册并核对来源。展示围绕完整应用链路展开：提交、保存、后台处理和持久化结果。模拟演示在 AI 边界回放已录制的哨兵模式答案，API、数据库和 worker 正常执行。

## Slide 2: Problem and delivered scope

Owners need a practical way to find instructions in a long manual and check what supports an answer. We support one Chinese manual, single-turn questions and saved history. Our intended value is easier navigation and source checking. We kept vehicle control, multiple vehicle versions and public accounts outside the project scope. That focus lets us explain and test the complete workflow instead of presenting a large collection of disconnected features.

中文彩排提示：痛点是长手册难查、回答依据难核对。交付范围为一本中文手册、单轮问答和历史记录。系统不控制车辆，不扩展多车型或公共账户，重点验证连贯的核心流程。

## Slide 3: One integrated system path

The browser sends a question to FastAPI. One PostgreSQL transaction commits both the question and pending job before HTTP 202. A separate worker claims that job and calls the AI service. The real adapter connects to the existing AutoDL retrieval and model pipeline. The presentation adapter replays a dated response at the same boundary. Both paths validate and persist the returned envelope through the same worker and database code. The browser then reads the stored answer.

中文彩排提示：浏览器经 API 提交后，数据库先保存问题和任务，再返回 202。worker 独立领取任务并调用 AI 服务。真实适配器对接原有 AutoDL 流程，演示适配器在同一边界回放录制答案。校验、保存和前端读取使用相同的核心代码。

## Slide 4: AI contribution and source integrity

The real pipeline combines BM25 and vector retrieval, BGE reranking and Qwen3 generation through vLLM. The model produces structured answer steps linked to retrieved source IDs. We preserve this model architecture and strengthen the engineering around it. The gateway and application validate reference IDs, page bounds, manual identity and checksums. Each new envelope records model, index and prompt identity. These checks make references auditable, while factual interpretation still needs human review.

中文彩排提示：原有 AI 流程包括混合检索、BGE 重排和 Qwen3 生成。期末重点加强外围工程与证据校验，没有替换模型架构。回答与来源 ID、页码、版本及哈希绑定；引用可核对，但语义正确性仍需人工评估。

## Slide 5: Reliability around the AI call

We keep the queue in PostgreSQL so input and job creation are atomic. Each claim has a unique token and an increasing generation. Conditional heartbeats protect active ownership, and recovery fences expired workers. A late result cannot overwrite a newer answer. Transient failures receive bounded retries, while invalid evidence fails immediately. Attempt history stays durable. The inference cache reduces repeated completed calls, but a crash can repeat model work before cache commit. Saved-state protection and model execution are separate guarantees.

中文彩排提示：问题和任务在同一事务内创建。唯一令牌、递增代次、心跳和过期恢复控制 worker 所有权，防止旧结果覆盖新结果。重试有上限，执行历史保留。模型调用可能重复，但保存结果受到所有权校验保护。

## Slide 6: Verification evidence

The updated Docker suite passed 58 unit, integration and real PostgreSQL tests. It covers concurrent workers and submissions, heartbeats, stale owners, retry limits, migrations and evidence corruption. New safeguards preserve the dated answer, reject unrecorded questions and keep recorded provenance explicit. Our captured demonstration also verifies queued SQL state before worker execution, persisted output, source-packet identity, JSON events, metrics and restart survival. These are application and integrity results. The replay does not measure new model quality or live-model latency.

中文彩排提示：Docker 内 58 项测试通过，覆盖并发、幂等、心跳、旧任务所有权、重试、迁移和证据一致性。模拟场景还验证了排队 SQL、持久化结果、摘录身份、日志、指标和重启恢复。本轮结果评价应用与引用完整性，不将回放解释为新模型质量测量。

## Slide 7: Simulated Sentry Mode demonstration

We first select the Sentry Mode scenario and submit the standard question. With the demonstration worker paused, we show that the question and job already exist in SQL. We then start the worker and correlate its claim and completion events. The answer recording passes through the current evidence contract and appears with two source excerpts. Next we submit an unrecorded question and show the explicit scope response. Finally we restart the Docker project and reopen the same saved answer and attempts.

中文彩排提示：先选择哨兵模式标准问题并提交，暂停 worker 后展示 SQL 中的排队状态。启动 worker，查看领取和完成事件，展示通过当前契约保存的录制答案与两条引用。再提交未录制问题，展示范围提示。最后重启 Docker 并再次打开同一份历史记录。

## Slide 8: Progression and next priorities

Our repository preserves the semester progression from W03 readiness and W04 architecture to W07 integration, the reliability upgrade and the final demonstration. The final delivery includes architecture and operations documents, decision records, a technical brief, a runbook, a presentation and dated evidence. The main product boundaries remain single-manual use, local access and an unmeasured factual benchmark. Our next priorities are human-reviewed factual evaluation, manual-version selection and public-user access controls. They strengthen the existing core before expanding the feature set.

中文彩排提示：仓库保留 W03、W04、W07、可靠性优化和期末交付的连续历史。材料包含架构、运维、决策记录、报告、演示和验收证据。后续优先做人工事实评估、手册版本选择和公共访问控制，再扩展更多功能。

## Review questions

- What executes in the simulated demo? The API, PostgreSQL, worker, validation, persistence and operations execute normally. Only the inference boundary replays a dated answer.
- Why keep a recorded mode? It gives reviewers a repeatable scenario with explicit provenance. It is separate from real inference.
- Has the core model changed? The original retrieval/reranking/model architecture remains; final work strengthens application reliability and evidence handling.
- Are valid citations an accuracy score? No. Semantic support requires human review.
- Does retry provide exactly-once inference? No. Ownership checks protect saved state, while model work may repeat around a crash.
- What remains outside scope? Multiple manuals, public accounts, complete tracing and a measured factual benchmark.
- Is MAIE6000C the product? It is the course. The product is Model 3 Manual Assistant.
