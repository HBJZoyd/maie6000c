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

Concurrency, heartbeat recovery, fencing, retry limits, migrations and corrupt evidence have deterministic coverage. Live smoke refuses non-live readiness. Broader load, controlled in-flight tunnel-loss recovery, public authorization and cross-manual evaluation remain future work. Synthetic answers are not factual or live-model evidence.

## Clean-start acceptance — additional executed run

Source: `6e885e9cc156789d23ebf1966b128a89d76859d1`; trace: `4f9fe954-2922-4b5e-9994-5cbf0d08bdfd`; 28 November 2026, 21:49 HKT.

| Check | Observed result |
|---|---|
| Git clone without local hardlinks | New checkout from local pending-release Git source; exact commit recorded |
| Initial checkout/config | Clean status; no `.env`; example-generated configuration |
| Isolated PostgreSQL | Zero existing questions before submission |
| Real readiness | API/database/RAG ready; mode live |
| New live request | HTTP202; queued SQL before worker; real A100 answer; gateway 5.39 s |
| Persistence/restart/idempotency | Passed; same saved answer and attempts after restart |
| New model-process counter snapshot | 1 successful request; 2537 prompt / 265 generation tokens |
| Verification cleanup | Compose down exit0; no `-v`; development stack untouched |
| Startup regression contracts | 4 passed with explicit isolated Docker/HTTP test doubles |
| Launcher rollback probe | unavailable falsely accepted exit0 → refused exit1 → original acceptance exit0; exact hash restored |

See `evidence/clean-start/`. This adds a repeated Sentry trace, not a third distinct question or an accuracy benchmark. It validates the local application/database against an already provisioned GPU; it is not cold reconstruction of private assets, cache-free image building or independent second-person review.

## Published GitHub clone and idle-tunnel drill — additional verification

The public repository was freshly cloned at `feb29e5d833345f283c35195a70e7f57f33e65d6` into another absent directory; `.env` was absent, Git status clean, and the new isolated PostgreSQL database initially contained zero questions. At 21:57–21:58 HKT, new request `9d80b78f-b158-40b4-9671-92e12538957e` passed queued SQL, actual A100 generation, citations, saved state, idempotency and restart. Gateway duration was 3.34 s. The collector and no-volume-deletion cleanup both exited0. See `evidence/remote-clean-start/`.

The restarted model's counter snapshot now shows 2 successful requests, 5074 prompt tokens and 624 generated tokens. This cumulative snapshot includes the earlier clean-start request; do not add it to that process's first snapshot as if they were independent totals. Distinct question count remains two overall.

Separately, stopping/restoring the local SSH forward produced actual readiness transitions ready/live → unavailable/unknown → ready/live while API/database remained ready. No in-flight job was interrupted; retry-under-interruption, factual quality and capacity are not established by this drill. Source runtime hashes are checked unchanged across the final evidence-only commit.
