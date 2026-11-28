# W13 GitHub and Canvas Handoff

Publisher: **C0216RC / RUICHAO CHEN**.
Repository: https://github.com/HBJZoyd/maie6000c.
Branch: codex/w13-final. Required checkpoint: w13-final.

## Verify the local delivery

In Windows CMD:

```cmd
cd /d "E:\Users\PC\Desktop\maie6000c"
git status --short
git log --graph --oneline --decorate -8
git rev-parse w13-final~0
```

The unrelated pre-existing file `tatus --porcelain` is not part of this submission.
Do not add private configuration, models, indexes, databases or environment dumps.

## Authenticate and publish

Browser and Git logins are separate. Authenticate C0216RC and complete the
GitHub authorization page with that account:

```cmd
git -c http.sslVerify=true credential-manager github login --username C0216RC --device --no-ui
```

C0216RC needs push access to the team repository. Do not silently use another
account. Once the reviewed final commit and local tag are ready, publish both:

```cmd
git -c http.sslVerify=true -c credential.username=C0216RC push https://C0216RC@github.com/HBJZoyd/maie6000c.git HEAD:refs/heads/codex/w13-final
git -c http.sslVerify=true -c credential.username=C0216RC push https://C0216RC@github.com/HBJZoyd/maie6000c.git refs/tags/w13-final
git -c http.sslVerify=true ls-remote origin refs/tags/w13-final "refs/tags/w13-final^{}"
```

Do not force-update an already published tag. The peeled annotated tag `^{}`
must equal `git rev-parse w13-final~0`. Use that full commit SHA in Canvas,
not the annotated tag object's SHA. Check the remote branch and CI after pushing.

## Canvas text

The generated local CANVAS_SUBMISSION.txt contains the filled commit SHA after
the checkpoint is prepared. Verify remote publication before pasting it:

```text
Repository: https://github.com/HBJZoyd/maie6000c
Required tag: w13-final
Tagged commit SHA: <full verified commit SHA>
Primary artifact: submissions/week13/README.md
Team name: Odie
Final demo readiness note: Docker demonstration ready. The fixed Sentry Mode scenario replays a dated answer while the API, PostgreSQL, worker, persistence, reference checks, logs, metrics and restart recovery execute normally. The repository includes the AutoDL RAG integration and separately dated W07 real-inference evidence. The simulated run evaluates engineering behavior rather than new model generation quality.
```

One official team submission is sufficient if Canvas uses group submission.
GitHub publication does not itself submit Canvas. Slides support the working
system demonstration; use the recorded-mode label when presenting it.
