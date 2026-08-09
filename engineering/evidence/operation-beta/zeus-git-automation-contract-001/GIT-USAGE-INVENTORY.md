# Git Usage Inventory

## Starting position

- Repository: `/data/engineering/repositories/homelab`
- Branch: `main`
- `HEAD == origin/main`: `e7e48ab6b523d94e73d40fb4311f86bc7118b0b1`
- Index: empty at start and after qualification.
- Existing dirty and untracked lifecycle/Class-C work was preserved.

## Current-path classification

| Surface | Observed use | Classification | Disposition |
|---|---|---|---|
| `scripts/zeus` platform/doctor/authority status | `rev-parse`, `branch`, and status-derived repository facts | DUPLICATE_REPOSITORY_PROJECTION; HUMAN_OUTPUT_BOOLEAN | Routed through `repository_projection.project`; authority status now fails closed instead of treating `HEAD` as the published baseline. |
| `next_action.py` legacy compatibility resolver | repository identity, HEAD, branch, published baseline | IMPLICIT_REFS; DUPLICATE_REPOSITORY_PROJECTION | Current fallback now consumes the canonical live projection; historical OA logic remains compatibility-only. |
| `mission_verification_controller.py` | repository identity, HEAD, branch, EOS/baseline | DUPLICATE_REPOSITORY_PROJECTION | Basic live facts now consume the canonical projection; mission provenance remains in the specialized baseline resolver. |
| `repository_projection.py` | `rev-parse --verify`, `branch --show-current`, `status --porcelain=v2 -z`, NUL path primitives, `diff --quiet`, `merge-base --is-ancestor` | MACHINE_SAFE | New canonical implementation. |
| `canonical_baseline.py` | exact commit plumbing and ancestry for receipt provenance | MACHINE_SAFE; SPECIALIZED_PROVENANCE | Retained as the receipt-lineage validator; no human output is parsed. |
| `state_sync.py` | exact HEAD/branch/remote plumbing for deterministic EOS rendering | MACHINE_SAFE | Retained as EOS generation implementation. |
| `operations.sh`, `state.sh`, `platform.sh` | human-oriented status text in legacy operator inventory/readiness renderers | LEGACY_COMPATIBILITY / HUMAN_OPERATOR_OUTPUT | Deferred from broad shell refactor; not a machine consumer of the new Zeus projection. Recorded for follow-up. |
| OA gate modules and historical fixtures | fixed tags, mission IDs, or historical baseline test vectors | HISTORICAL_ONLY / COMPATIBILITY | Not rewritten by this task. |

No current projection relies on parsing `git log` text. Network publication and
operator-interactive SSH prompting remain outside this read-only projection.
