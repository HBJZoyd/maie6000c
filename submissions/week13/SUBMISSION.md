# GitHub and Canvas handoff

Team Odie. Course MAIE6000C. Latest publisher: **HBJZoyd**.

## Retained history and release names

- `w13`: latest improvements and updated materials.
- `w13-final`: required annotated release tag, not another development branch.
- `w13-1`: old simulated final `d85b72023dcbf2fbb2887dc077b012d7bf2aaae3`.
- `w13-2`: previous real final `6fbec0338230029203ce687853b546580f7ef849`.
- `w13-reliability`: unchanged ZHANG Yiming optimization `b6c5ef37a7b4be7d786a7e79e767528fa96c499c`.

Old authors, commits, simulated evidence, main and W07 are retained. HBJZoyd publishes the new changes; this does not relabel earlier contributors. The unrelated local untracked file is not a deliverable.

## Verify the exact checkpoint

```powershell
git rev-parse 'refs/tags/w13-final^{commit}'
git -c http.sslVerify=true ls-remote origin refs/heads/w13 refs/tags/w13-final 'refs/tags/w13-final^{}'
```

Use the full peeled commit SHA, not the annotated tag object. Latest branch and tag must agree. Verify CI and authenticated publisher HBJZoyd; commit author and push identity are separate facts. Publication uses explicit leases after rereading remote refs, leaving other milestones unchanged.

## Canvas six fields

```yaml
Repository: https://github.com/HBJZoyd/maie6000c
Required tag: w13-final
Tagged commit SHA: FULL_VERIFIED_PEELED_SHA
Primary artifact: submissions/week13/README.md
Team name: Odie
Final demo readiness note: >-
  Real A100 inference and fresh local checkout/database startup were verified.
  Validation covers queued persistence, worker processing, actual generation,
  manual citations, idempotency, restart recovery, logs and metrics. There are
  59 Python engineering/PostgreSQL tests and four separate PowerShell startup
  contracts, plus live GPU evidence. Authorized private GPU assets and an SSH
  tunnel remain prerequisites; factual accuracy is not a measured benchmark.
```

The generated final Canvas text stays outside the commit so it can contain the exact new SHA without a self-referential hash. Refresh runtime readiness before presenting: a dated successful run is not a permanently hosted service. GitHub publication is not Canvas submission; the team performs the official submission and demonstration.
