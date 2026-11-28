# Real demonstration runbook

## Preconditions
Use authorized GPU assets, the genuine Mongo snapshot, rebuilt 6102-row index, current adapters and localhost SSH forwarding. Do not use fixture/replay servers. A GPU stopped after delivery must first be restarted through the platform; see operations.

1. Start the GPU supervisor and wait for real model/gateway readiness.
2. Start local Docker with `scripts/start.cmd -Mode Remote`.
3. Check `/system/status`: API/database/RAG ready, mode live. Open `/app` and verify the connected indicator.

## Working-system sequence
- Submit: **Model 3 如何开启哨兵模式？在家停车时可以自动关闭吗？**
- Explain that HTTP 202 follows committed question/job records, not a browser-generated answer.
- Inspect the saved question, independent worker attempt and cited answer; open hash-checked manual pages and expand excerpts.
- Correlate its ID with worker JSON events, cloud chat-completion/`rag_completed` logs and request/token metrics.
- Reopen history. The collector below proves queued SQL before worker execution and restart survival.

```powershell
python scripts/collect_final_evidence.py --mode live --base-url http://127.0.0.1:8000 --project maie6000c --compose-file compose.yaml --pause-worker --restart --timeout 900 --output artifacts/live-rehearsal
```

The collector creates a new real request and restarts only the named local stack, preserving volumes. Final core trace: 728dcdf5-79b7-42ca-94d1-0405e3f963a3. Charging trace: 1118e376-ff76-42fd-84e0-2ec6d6c71cea.

## Failure and closing
If unavailable, show that state, retain attempts and restore dependencies before retrying. Never switch silently to a recording. Saved history is historical evidence, not a new model call. Citation validity is not factual correctness or vehicle safety.

After engineering, remove temporary keys/forwarding and use platform power-off for A100/source, verifying stopped status. Keep data disks and database volumes. Do not set automatic timers or release instances.
