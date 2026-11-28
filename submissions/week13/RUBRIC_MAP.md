# W13 Rubric and Evidence Map

This index maps implementation and evidence to the supplied rubric. It does not assign a score.

| Criterion | Weight | Implementation and review evidence |
|---|---:|---|
| Problem framing and scope | 10 | One Chinese manual, owners/support staff, lookup, history and explicit exclusions |
| Functional completeness | 20 | Browser/API/SQL/worker/AI boundary/results; W07 real inference and repeatable recorded demo |
| Engineering quality | 20 | Service boundaries, shared schemas, migrations, fenced claims, retries and idempotency |
| Architecture and decisions | 15 | Architecture notes, ADRs 0001-0005, technical brief and explicit replay boundary |
| Testing and validation | 10 | Unit/integration/PostgreSQL suite, queued/completed SQL, source hashes, scope response and restart |
| Documentation and operability | 15 | Startup/runbook, JSON logs, health/readiness, metrics, attempts and captured evidence |
| Progression and discipline | 10 | W03/W04/W07 continuity, reliability upgrade and w13-final checkpoint |

## Evidence interpretation

The simulated demo executes the application path and replays a dated answer at the
inference boundary. The UI and saved provenance identify this mode. It validates
engineering behavior rather than new model quality or live-model latency. W07
real inference remains a separate dated evidence set. The main product limits
are single-manual scope, local access and an unmeasured factual benchmark.

## Reviewer entry points

- API and persistence: services/api/app/main.py, services/common/models.py.
- Reliability: services/worker/app/main.py, tests/postgres/.
- Real AI: scripts/rag_gateway.py, RAG/src/, runtime and asset helpers.
- Presentation adapter: scripts/replay_rag.py, scripts/demo_data/, compose.demo.yaml.
- Source checks: scripts/rag_evidence.py, services/common/schemas.py.
- Demonstration: SIMULATED_DEMO.html and DEMO_RUNBOOK.md.
- Verification: evidence/validation.json and evidence/replay/.
