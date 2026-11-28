# ADR0007 — Require live readiness and verify a fresh local deployment

Date: 28 November 2026. Status: implemented and executed.

The prior Remote launcher treated healthy containers as successful startup even when the external GPU was unavailable. This concealed an operational precondition. Remote success now requires API/database/RAG ready and mode live, and an explicit API port is used consistently for Compose and the check. Configuration-only preflight remains separately labelled.

A clean-start verifier clones exact source into a new directory, refuses old config/project/ports, requires zero initial questions and executes the existing live collector with queued SQL and restart checks. It uses a separate Compose database and never silently selects a fixture. Four isolated PowerShell contracts cover failure/fixture/live/configuration-only behavior, with explicit test doubles. Actual inference is supported separately by live evidence.

The trade-off is fail-fast operator feedback rather than pretending the repository alone distributes private GPU assets. Authorized pre-provisioned weights/manual/environment and verified SSH remain explicit prerequisites. The executed pending-release source is recorded; no cache-free build, independent reviewer, broad factual accuracy or general disaster-recovery claim is made.
