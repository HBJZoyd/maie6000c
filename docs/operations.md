# Operations — real model deployment

## Reproduction boundary

The API, AI HTTP service, worker and PostgreSQL build from this repository. A
clean clone creates its own configuration and empty database, then calls a real
external GPU backend. Authorized weights, the complete manual and databases are
not redistributed in Git. See [clean-start reproduction](reproducibility.md).

Prerequisites: Windows PowerShell 5.1+, Git, OpenSSH, Python 3.11+ standard library,
Docker Desktop Linux containers, network access and authorized GPU assets.
The observed GPU environment is A100 40GB / Python 3.12.13 / torch 2.7.0+cu126 /
vLLM 0.9.0.1 / transformers 4.51.1 / pymilvus 2.5.9. Do not blindly upgrade it.
There is no A800 execution claim. Powering on an instance does not start its model.

MongoDB, vLLM and RAG bind loopback. Authenticated SSH forwards only the gateway;
local application ports also bind loopback. Never commit credentials, databases
or private runtime configuration. Original `infer.py` and `src/` stay unchanged.

## 1. Verify the provisioned GPU release

In the platform's authenticated Jupyter terminal:

```bash
export PYTHONDONTWRITEBYTECODE=1 MONGO_HOST=127.0.0.1
RAG_ROOT=/root/autodl-tmp/RAG
PYTHON=/root/miniconda3/envs/rag/bin/python
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
"$PYTHON" "$RAG_ROOT/start_rag.py" --root "$RAG_ROOT" --check-assets-only
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Compare the trusted-console SSH fingerprint before accepting a new host key
interactively. Scripted connections require a previously verified `known_hosts`
entry; never disable host-key or TLS verification. Asset preflight verifies hashes
without loading GPU modules. The live gateway also verifies package versions,
PDF identity and the complete Mongo snapshot. Do not recapture a manifest to hide
an unexpected change. For a new target, provision the authorized pinned environment
and assets before these steps; Git alone intentionally does not distribute them.

The manual is 255 pages, version `sha256-baaf110b1b70cdf6`, PDF SHA256
`baaf110b1b70cdf6f2493e071ed5ac3248bed732635ba74f77ae376dae659716`.
The release includes 6102 genuine Mongo records and a rebuilt 6102-row Milvus index.

## 2. Start real services and forwarding

From the checkout in terminal A, substitute current platform SSH host/port:

```powershell
scripts/connect-rag.ps1 -SshHost SSH_HOST -Port SSH_PORT `
  -RagDir /root/autodl-tmp/RAG `
  -RemotePython /root/miniconda3/envs/rag/bin/python -ManageServices
```

This uploads five adapters only; it downloads no models and installs no packages.
Keep the terminal open. Wait for `Real RAG backend ready`: vLLM allows up to 900
seconds and gateway initialization another 300. Mongo is restored only if empty,
then compared with its snapshot. Mongo uses `runtime/mongo`; Milvus uses a writable
`runtime/<index_version>` copy rather than changing the hashed release. Observed
vLLM memory fraction is 0.55, not a capacity benchmark.

If the supervisor already runs in Jupyter, do not start a second gateway:

```powershell
scripts/connect-rag.ps1 -SshHost SSH_HOST -Port SSH_PORT -TunnelOnly
```

Optional `-IdentityFile PRIVATE_KEY_PATH -KnownHostsFile KNOWN_HOSTS_PATH` uses
existing authorized access. Otherwise OpenSSH prompts for the existing password;
no password is stored. Temporary-key installation is a separate approved action.

## 3. Start the real local application

In terminal B:

```powershell
scripts/start.cmd -Mode Remote
Invoke-RestMethod http://127.0.0.1:8000/system/status
```

The launcher creates `.env` from `.env.example` only if absent, drains old workers
before additive migrations, builds containers and checks actual readiness. Only
API/database/RAG ready with `mode=live` prints `REAL MODEL READY`. Alive containers
alone are not success. `-CheckOnly` checks configuration, not model readiness.
Explicit `-ApiPort` overrides the API host port; otherwise existing settings are
preserved. Open `http://localhost:8000/app`.

Historical Offline/Demo modes remain labelled simulations in separate projects;
they never silently replace Remote mode. Their evidence is not new inference.

## 4. Observe and verify

```powershell
docker --context default compose -p maie6000c -f compose.yaml ps
docker --context default compose -p maie6000c -f compose.yaml logs --tail 80 worker
python scripts/collect_final_evidence.py --mode live --base-url http://127.0.0.1:8000 --project maie6000c --compose-file compose.yaml --pause-worker --restart --timeout 900 --output artifacts/live-rehearsal
```

Use a planned demo window: the collector pauses/restarts only the named project,
preserving volumes. Inspect `/questions/ID/attempts`, `/jobs/ID`, `/metrics` and GPU
`runtime/rag.log`, `runtime/llm.log`, `runtime/mongo.log`. Correlate the question ID
with worker completion and a new model request/token increase. Gateway duration
includes retrieval/generation, not isolated model latency.

| Symptom | Recovery | Acceptance |
|---|---|---|
| API/database ready, RAG unavailable | Restore tunnel and GPU supervisor; inspect logs | ready/live, then rerun launcher |
| SSH host key differs | Compare trusted-console fingerprint; stop if unexplained | Verified host; never bypass warning |
| Model exits / CUDA missing | Check GPU mode, pinned environment and `llm.log` | Configured model appears in `/v1/models` |
| Asset/Mongo mismatch | Preserve evidence and restore pristine authorized asset, not expected hash | Exact checks pass |
| Milvus URI/schema mismatch | `.db` suffix; stored text limit 8192, not legacy 512 | Retrieval and real question succeed |
| Invalid evidence | Inspect attempts, IDs/pages/manual/checksums; never fabricate answers | Validated answer or honest failure |
| Timeout / tunnel loss | Restore dependency before manual retry; automatic retries are bounded | Completed attempt; idempotency retained |
| Port/project occupied | Choose unused ports/new project | Existing stacks/data untouched |

## 5. Recovery, data retention and stopping

Never use `down -v`, reset a healthy index, release data disks or use `--delete`
against deployed assets as normal operations. The index helper refuses a nonempty
baseline. Its retained baseline/patch/ledger/rollback proves 0 → 6102 → 0 and exact
hash recovery. Launcher rollback tests are explicitly isolated test doubles, not
model evidence.

For application rollback, stop its worker and test a retained commit against a
separate database restored from an operator backup before switching traffic.
Do not run older unfenced workers against the upgraded database or assume safe
destructive downgrades. The delivery proves restart retention and index rollback,
not general disaster recovery; a backup/restore drill remains separate work.

Stop a local project with `docker compose -p PROJECT -f compose.yaml down` without
`-v`; retain named volumes. Ctrl+C stops a foreground tunnel/supervisor; the latter
terminates only children it created. Remove approved temporary keys after use.
For billing use platform power-off and verify stopped status; OS shutdown alone
is not proof. Do not set automatic timers or release instances/data disks. Agree
any presentation availability window explicitly rather than leave indefinite fees.

## Honest limits

This is reproducible local application startup with a provisioned real GPU, not
an offline all-local inference distribution. Asset entitlement, one manual,
local access, incomplete human factual evaluation and no controlled capacity
study remain explicit. Citation integrity is not semantic correctness or safety.
