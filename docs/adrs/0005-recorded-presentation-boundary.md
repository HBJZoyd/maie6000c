# ADR 0005: Recorded presentation adapter

Status: accepted. Date: 27 November 2026.

## Context

The final presentation needs a repeatable Sentry Mode example with inspectable
answers and operational behavior. The core product path remains browser, API,
PostgreSQL, worker, AI service and RAG gateway. Retrieval and model generation are
an explicit HTTP boundary, so the presentation can control that boundary without
replacing the application path.

## Decision

Add an explicitly selected recorded adapter in a separate `odie-demo` Docker
project. It replays the exact standard question and answer from the dated W07
record, packages two source-excerpt pages and wraps them in the current evidence
contract. The original source page numbers remain in titles, while PDF page links
refer to the two-page demonstration packet. The adapter reports fixture provenance
and `demo_kind=recorded-replay`. It refuses unrecorded questions and cannot run
in production. The normal AutoDL adapter and generic engineering fixture remain
available, with no automatic fallback between them.

## Consequences

HTTP submission, relational persistence, asynchronous execution, ownership checks,
result validation, logs, metrics and restart recovery run as implemented. The
demonstration's answer is a recording, so this run measures the application path
and envelope integrity rather than new retrieval, generation quality or live
model latency. This distinction is recorded in the UI, evidence and presentation.
The demo introduces no alternate training, retrieval algorithm or production model.
