# Publication Verification Report

Date: 2026-07-30

| Verification | Result |
| --- | --- |
| `git rev-parse HEAD` | `5decaed25c8e3489b49f7dcb032eb27ffd7c783e` |
| `git rev-list -n 1 ZEUS-CONVERGENCE-RUNTIME-BASELINE-1.0` | `5decaed25c8e3489b49f7dcb032eb27ffd7c783e` |
| HEAD equals peeled tag commit | PASS |
| Annotated tag object | `3794b02815c9da0bc8909a4132e6b1fa5f8f46b9` |
| `origin/main` | `5decaed25c8e3489b49f7dcb032eb27ffd7c783e` |
| `origin` peeled tag reference | `5decaed25c8e3489b49f7dcb032eb27ffd7c783e` |
| Tag annotation | `Immutable certified Zeus runtime baseline for Operational Alpha implementation.` |
| Publication-boundary exclusion scan | PASS |

The local branch, `origin/main`, and the peeled annotated tag resolve to the
same published commit. The tag object is intentionally distinct from the
commit object because the tag is annotated.
