# ADR 0004: Separate engineering fixture and real GPU startup

Status: accepted for offline operation; GPU deployment rehearsal pending.

AutoDL is unavailable during this development pass. Provide an isolated Compose
project with real PostgreSQL/API/worker boundaries and explicitly synthetic output.
Its UI, API provenance and readiness identify fixture mode, and production mode
rejects the fixture CLI. No automatic fallback from a failed GPU request is allowed.

Keep the provisioned GPU architecture, but add asset inventories, MongoDB export/
empty-target restore, runtime compatibility checks and a foreground supervisor.
Application dependencies and container bases are pinned. Weights and original
manual assets are provisioned privately with checksums, not committed to Git.

This allows local engineering verification while the GPU is off. It does not prove
GPU portability, JSON generation quality or factual accuracy. Those checks remain
explicit prerequisites for a final real-AI readiness claim.
