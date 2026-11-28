# Reliability upgrade and final integration

ZHANG Yiming's commit `b6c5ef37a7b4be7d786a7e79e767528fa96c499c` remains the final commit's parent. It supplies atomic question/job persistence, idempotency, fenced worker claims, heartbeats, bounded retries, attempt history and versioned evidence validation.

The final delivery retains these mechanisms around real GPU inference. On28 November2026, a Sentry question was observed queued in SQL before worker execution, answered by A100/Qwen3 and retained after local-stack restart. A charging question passed an additional live smoke test. See the final evidence index rather than obsolete offline startup instructions.

At-least-once inference remains explicit. Fencing protects saved state from stale completion, not against all repeated GPU work after a crash. Legacy W07 answers remain readable without invented metadata.

Historical fixture/replay runs and their explicit mode labels are preserved, separately from the real default deployment. Current verification is59 passing unit/integration/PostgreSQL tests plus one real-GPU smoke test. Neither is a vehicle-answer accuracy score.
