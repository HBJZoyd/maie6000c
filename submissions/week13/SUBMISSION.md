# GitHub and Canvas handoff

Team Odie. Course MAIE6000C. Publisher **C0216RC / RUICHAO CHEN**.

The existing final commit `d85b72023dcbf2fbb2887dc077b012d7bf2aaae3`, its parent `b6c5ef37a7b4be7d786a7e79e767528fa96c499c` (ZHANG Yiming), main and W07 are preserved. The user requested append-only publication while retaining all prior simulated materials. The release keeps the branch name codex/w13-final, the tag name w13-final and the C0216RC / RUICHAO CHEN identity. Existing commits are not deleted. The unrelated pre-existing `tatus --porcelain` is not a deliverable.

## Verify publication
Use the peeled commit, not the annotated tag object:

```powershell
git rev-parse 'w13-final^{commit}'
git -c http.sslVerify=true ls-remote origin refs/heads/codex/w13-final refs/tags/w13-final 'refs/tags/w13-final^{}'
```

Remote branch and peeled tag must agree. Verify CI and publisher C0216RC; author and authentication are distinct. The branch advances by a new child commit. The same named annotated tag is moved to that commit with an explicit lease after rereading remote refs; main and w07-midterm remain unchanged.

## Canvas six fields
- Repository: https://github.com/HBJZoyd/maie6000c
- Required tag: w13-final
- Tagged commit SHA: full 40-character verified peeled commit from the commands above
- Primary artifact: submissions/week13/README.md
- Team name: Odie
- Final demo readiness note: Real A100 end-to-end, queued SQL, citations, idempotency and restart verified on 28 November 2026. Another run needs authorized private assets and GPU/tunnel. Power-off after engineering avoids charges. Factual accuracy is not a measured benchmark.

The generated final Canvas text is outside the commit so it can contain the exact new SHA without a self-referential hash. GitHub publication is not Canvas submission; do not submit Canvas automatically.
