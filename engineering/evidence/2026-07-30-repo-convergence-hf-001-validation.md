# REPO-CONVERGENCE-HF-001 Validation Report

Date: 2026-07-30

Validation boundary: local repository convergence candidate

## Preconditions

| Check | Result |
|---|---|
| Repository identity | PASS |
| Root and remote identity | PASS |
| Branch and upstream relation | PASS |
| ARCH-0001 Draft 1.6 identity | PASS |
| ADR-0001 Draft 1.3 identity | PASS |
| SPEC-0002 Draft 1.3 readiness input | PASS |
| AQR-0001 Draft 1.1 convergence input | PASS |
| AQR inventory/backlog reviewed | PASS |
| Original 435-path status cardinality | PASS |
| Empty initial staging area | PASS |

## Protected SHA-256 values

| Path | SHA-256 | Result |
|---|---|---|
| `docs/architecture/ARCH-0001-ENGINEERING-CONVERGENCE-ASSESSMENT.md` | `a3965a1797d049ca2dc5d8a1d408556ad187d7aa49c4645d73eb52163ac0d9dd` | unchanged |
| `docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md` | `bc3749695802757f346ba8c144c7331dbc9cdac931d0a39157066c4df68997c3` | unchanged |
| `docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md` | `0fa1f3153361f18e72be6e8500ce0fb96cfdc5ade2d41a7ab9462b2e7c574741` | unchanged |
| `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md` | `5d9f1d06baf0425adefa0c5e2f9559f42e017cf2f73ace4093cac00e20b15b35` | unchanged |

## Pre-persistence validation

| Command/check | Result |
|---|---|
| `git diff --cached --check` | CLASSIFIED — 129 preserved/imported paths; 62 trailing-whitespace lines are Markdown hard breaks and 92 paths have an extra blank EOF line; exact evidence/archive bytes preserved |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_controlled_documents.py` | PASS — 2,825 passed, 0 failed |
| `PYTHONDONTWRITEBYTECODE=1 scripts/verify.sh` | PASS — 28 passed, 0 warnings, 0 failures |
| `git fsck --no-dangling --no-progress` | PASS |
| Historical archive `sha256sum -c SHA256SUMS` | PASS — 7 entries |
| Historical source/archive byte comparisons | PASS — 5 of 5 |
| Unique/non-overlapping original inventory assignment | PASS — 435 of 435 |
| Unignored cache/bytecode/temp artifacts | PASS — 0 |
| Tracked cache/bytecode/temp artifacts | PASS — 0 |
| Private-key/token marker scan outside ignored Runtime | PASS — 0 matching files |
| Symlinks among candidate deviations | PASS — 0 |
| Submodules | PASS — 0 |

The indexed whitespace diagnostics are not working-tree dirt and do not affect
checkout reconstruction. Rewriting them would alter historical review/archive,
engineering evidence, WOP evidence, and related preserved inputs. The
convergence reports themselves have final newlines and no trailing whitespace.

## Candidate-boundary validation

Before local persistence, the exact staged path set shall satisfy:

```text
expected paths: 441
original paths: 435
intrinsic outputs: 6
deletions: 0
renames: 0
unexplained paths: 0
```

The candidate path set is the union of:

1. every exact path in the SHA-bound AQR repository inventory; and
2. the six exact intrinsic-output paths in the Repository Disposition Matrix.

Any staged-set mismatch stops persistence.

## Required post-persistence validation

The local persistence operation is complete only after all of these pass:

- committed path set equals the 441-path candidate boundary;
- commit tree equals the pre-commit candidate tree;
- working tree and index are clean;
- protected SHA-256 values remain unchanged;
- a clean local clone resolves the same commit and tree;
- controlled-document validation passes in the clean clone;
- repository verification passes in the clean clone;
- clone status remains clean after validation; and
- no publication, tag, push, synchronization, activation, approval, or
  promotion side effect occurred.

The immutable local commit/tree locators and post-persistence command totals
are returned to the operator after those checks complete. The commit is a
repository candidate locator only, not controlled publication or Active
Baseline evidence.
