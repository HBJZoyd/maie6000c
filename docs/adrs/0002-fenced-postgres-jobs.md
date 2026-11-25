# ADR 0002: PostgreSQL jobs with per-attempt ownership

Status: accepted for the W13 preparation implementation.

The existing transaction already commits input and work together. Retain that
database queue to preserve a simple deployment. Row locks and SKIP LOCKED handle
competing consumers. A UUID claim token and generation fence completion/failure
writes after lease expiry. Heartbeats and durable attempt records support recovery
and debugging. Transient failures use a bounded scheduled retry policy.

An external broker is deferred until measurements justify another dependency.
HTTP submission uniqueness and completed-result replay reduce duplicate work,
but a crash before the inference cache commits can repeat GPU computation.
We claim at-least-once execution with conditional application writes, not exactly-once.
Validation includes PostgreSQL concurrent claim and submission tests, stale-owner
tests, retry limits and migrations preserving W07 answers.
