\# W03 Individual Readiness Lab



\## What I changed

\- Added a `version` field to the shared `HealthResponse` schema in `services/common/schemas.py`.

\- This makes both the API service and AI service health endpoints return a version identifier.



\## How I verified it

\- Rebuilt and started the stack with `docker compose up --build`.

\- Opened `http://localhost:8000/health/live` and confirmed the response includes `"version": "0.1.0"`.

\- Opened `http://localhost:8100/health/live` and confirmed the same.

\- Ran the existing tests and they passed.

\- Ran `docker compose down` to clean up.



