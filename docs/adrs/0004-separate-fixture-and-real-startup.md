# ADR 0004 — Keep real and simulated startup explicit

Status: updated at the user’s preservation request, 28 November 2026.

The default launcher selects the real Remote deployment. The previous Offline and Demo modes remain available only by explicit selection, in separate odie-offline/odie-demo projects and volumes. Their UI and returned provenance identify synthetic or recorded output. Production rejects both modes, and unavailable real inference never silently falls back to simulation.

Original simulated runs and historical reports/PPT/script are retained beside the new A100 live evidence. Their labels and measurement boundaries remain intact. Deterministic tests continue to use controlled doubles.
