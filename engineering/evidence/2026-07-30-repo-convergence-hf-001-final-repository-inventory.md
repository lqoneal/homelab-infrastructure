# REPO-CONVERGENCE-HF-001 Final Repository Inventory

Date: 2026-07-30

## Candidate identity

| Property | Value |
|---|---|
| Repository | `homelab-infrastructure` |
| Repository root used for construction | `/data/engineering/repositories/homelab` |
| Remote identity | `git@github.com:lqoneal/homelab-infrastructure.git` |
| Branch | `main` |
| Starting commit | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Original deviations | 435 |
| Intrinsic convergence outputs | 6 |
| Expected persisted path boundary | 441 |
| Deletions | 0 |
| Renames | 0 |
| Submodules | 0 |
| Candidate architecture lifecycle | Draft / Pending approval / Pending controlled persistence |

The local convergence commit and its tree object are immutable Git locators.
They persist repository content only. They do not change the Draft,
approval-status, controlled-persistence, publication, activation, or promotion
meaning declared by the architecture documents.

## Content inventory

| Content cohort | Paths | Final treatment |
|---|---:|---|
| Controlled architecture, inputs, and SPEC/AQR evidence | 12 | retain or preserve exact qualified bytes |
| Historical archive | 8 | preserve in place |
| Superseded historical decision artifact | 1 | preserve in place |
| Engineering reviews and redesign assessments | 14 | retain |
| Other central evidence | 62 | retain |
| Generated architecture metadata | 8 | retain as generated reference data |
| Other controlled/supporting documents and planning | 14 | retain |
| Registry/state/authority/projection candidates | 7 | retain without activation or synchronization |
| Runtime decision/evidence | 48 | preserve |
| WOP packages and local records | 172 | retain |
| Tests and qualification support | 39 | retain |
| Runtime/service/CLI/operations implementation | 50 | retain |
| Intrinsic convergence evidence | 6 | retain |
| **Total persisted path boundary** | **441** | **complete** |

Exact original paths are enumerated in the SHA-bound AQR source inventory.
Exact intrinsic output paths are enumerated in the Repository Disposition
Matrix. Together they form the complete local persistence boundary.

## Ignore inventory

| Check | Result |
|---|---:|
| Ignored file-level local/generated artifacts observed before persistence | 1,333 |
| Unignored cache/bytecode/temp artifacts | 0 |
| Tracked cache/bytecode/temp artifacts | 0 |
| Private-key/token marker matches outside excluded local Runtime | 0 |

The existing `.gitignore` correctly represents intentional local/generated
content:

- `.zeus/` repository-local Zeus Runtime;
- PMCT run, evidence, log, report, checkpoint, and artifact directories;
- Python bytecode and `__pycache__`;
- logs, `tmp/`, and `.cache/`; and
- local notification secret configuration.

No ignore-rule change was required.

## Final clean-state criteria

The persisted candidate is acceptable only when all of the following are
verified:

- `git status --porcelain=v1 --untracked-files=all` is empty;
- staged paths are zero;
- the committed path set equals the 441-path candidate boundary;
- indexed whitespace diagnostics are completely classified, with protected
  historical/evidence bytes preserved rather than silently normalized;
- controlled-document validation passes;
- repository verification passes;
- protected architecture digests remain unchanged;
- archive checksums and source/archive byte comparisons pass;
- a clean local clone resolves the same commit and tree;
- the clean clone has no tracked or untracked deviations after validation; and
- no tag, push, publication, synchronization, activation, or promotion occurs.

The corresponding command results and immutable locator are reported in the
Validation Report and final operator return.
