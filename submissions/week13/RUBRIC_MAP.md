# Rubric and evidence map

This maps the supplied rubric; it does not award a score.

| Criterion | Weight | Review evidence |
|---|---:|---|
| Problem/scope | 10 | One manual, owners/support staff, cited lookup/history and exclusions |
| Functional completeness | 20 | Real HTTP202 → SQL → worker → A100 Qwen3 → saved answer/references → restart |
| Engineering quality | 20 | Preserved idempotency, fenced claims, heartbeat, bounded retry and migrations |
| Architecture/decisions | 15 | Architecture flow, service boundaries, ADRs and target-only repair |
| Testing/validation | 10 | 59 engineering/PostgreSQL tests; 4 isolated PowerShell startup contracts; real GPU smoke and clean-start evidence; hash/rollback proof |
| Documentation/operations | 15 | Runbook, real evidence, logs, metrics, asset checks and shutdown |
| Progression/discipline | 10 | W03/W04/W07 retained, ZHANG Yiming history and existing final checkpoint preserved |

Review live summary, queued/completed SQL, attempts, actual cloud model events and charging smoke evidence. Citation integrity is not factual accuracy. Root README, architecture, operations, ADRs and this final directory are entry points.
