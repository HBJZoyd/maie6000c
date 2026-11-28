# Evaluation and measurement scope

## Observed on 28 November 2026
| Check | Result | Interpretation |
|---|---|---|
| Sentry, real model | answered; pages 39/115; gateway 5.77 s | One engineering trace |
| Charging, real model | answered; pages 142/144; gateway 3.94 s | Separate live smoke pass |
| Queued SQL before worker | passed | Input/job persisted before inference |
| Idempotency/restart | passed | Same request/result/attempts retained |
| Unit/integration/PostgreSQL | 59 passed; 2 warnings | Engineering coverage |
| Repair/rollback | 0 → 6102 → 0; exact restored hash | Recovery/patch integrity |

Two distinct live questions are **not** an accuracy benchmark. Valid IDs/checksums/pages establish envelope consistency, not semantic support. Gateway duration includes retrieval and generation; these samples establish neither percentiles nor capacity. The generated Sentry first instruction omits a UI-icon detail, illustrating why human review is still needed.

## Human-reviewed factual protocol — not completed
Use the exact hashed 255-page manual. Label expected pages before scoring. Include Sentry enabling/home exclusion, charging limit versus scheduling, Sentry limitations, touchscreen-restart prerequisites, tyre-pressure information, an ambiguous question, out-of-manual insurance pricing and a request to invent repair steps. These are evaluation inputs, not vehicle instructions.

Retain question ID, answer type, excerpts/pages, attempts, model/index/prompt versions and stage timings. Two reviewers should independently judge relevance, support for every step, qualifications and appropriate clarification/abstention. Retain disagreements and report per-question outcomes before generalizing. Confidence numbers or checksum passes are not calibrated accuracy.

Concurrency, heartbeat recovery, fencing, retry limits, migrations and corrupt evidence have deterministic coverage. Live smoke refuses non-live readiness. Broader load, controlled tunnel-loss recovery, public authorization and cross-manual evaluation remain future work. Synthetic answers are not factual or live-model evidence.
