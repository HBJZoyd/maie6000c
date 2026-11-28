# Clean-start reproduction

## Boundary

A new Git checkout and empty PostgreSQL database call an authorized, hash-verified
real external GPU backend. No development `.env`, database, weights or saved
local answers are copied. A fresh UUID/idempotency key prevents reuse of the
completed response of an earlier request.

Prerequisites: PowerShell 5.1+, Git, OpenSSH, Python 3.11+ standard library, Docker
Desktop Linux engine, network access and authorized GPU environment/assets.
Complete GPU startup/forwarding in [operations](operations.md) first. No
fixture/replay backend is accepted.

## Repeat from the release

```powershell
git -c http.sslVerify=true clone https://github.com/HBJZoyd/maie6000c.git odie-release
cd odie-release
git checkout --detach w13-final
# Terminal A: start/forward GPU as described in operations.md.
# Terminal B: choose a directory that DOES NOT exist and three unused ports.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-clean-start.ps1 `
  -CheckoutDirectory C:\odie-review-clean `
  -Revision w13-final -ProjectName odie-review-clean `
  -ApiPort 18000 -AiPort 18100 -DatabasePort 15432
```

The script defaults to the public repository. `-Repository` can select a local
Git object source for pending-release verification; that source is recorded and
must not be described as a remote-clone result. Use `-Revision FULL_SHA` to remove
ambiguity. `-Python FULL_PYTHON_PATH` selects the host interpreter. An existing
optional `RAG_API_TOKEN` process variable stays in ignored local `.env`, never
exported evidence.

## Executed checks

1. Refuse an existing checkout path/occupied ports; clone without local hardlinks.
2. Check out the exact commit; require clean Git status and absent `.env`.
3. Generate configuration from `.env.example`, with isolated ports/Compose project.
4. Build API, AI service, worker and new PostgreSQL; require ready/live and zero
   existing questions.
5. Pause worker, submit fresh input with HTTP202, observe queued SQL/no answer,
   resume worker and execute actual inference.
6. Validate/persist cited answer; verify PDF hash and idempotency; collect logs and
   metrics; restart the local stack and compare saved state.
7. Write `artifacts/clean-start/reproduction.json` and `live/` evidence. Default
   cleanup stops only this new project without deleting named volumes.
   `-KeepRunning` leaves it available. Neither option powers off the external GPU.

The original development stack/database are untouched. A failing stage fails the
command and retains partial evidence; it never substitutes an old recording.

## Limits

This proves fresh local application/database deployment with a provisioned GPU,
not recreation of private training assets or a cold asset download. Docker caches
may be used; no cache-free build claim is made. It is an executed procedure, not
an independent second-person review. Factual correctness and capacity require
separate evaluation. The final evidence report records source SHA and timestamps.
