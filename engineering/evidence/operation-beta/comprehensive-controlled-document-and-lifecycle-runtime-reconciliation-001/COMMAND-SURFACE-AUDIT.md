# Command Surface Audit

Observed current surfaces include:

- `zeus wop validate|lint|inspect`: source contract inspection.
- `zeus submit`: canonical P2 submission and explicit legacy compatibility.
- `zeus mission snapshot|verify|show|state|authority|blockers|next`: read-only mission projections where the selected runtime contains the relevant receipt/contract chain.
- `zeus admit`: P2-to-P3 admission boundary; not run in this handoff.
- `zeus bootstrap admission`: P4 admission-driven bootstrap; not run.
- `zeus codex start|reconcile`: provider/session preparation and reconciliation.
- `zeus execution-start begin`: controlled mission-work start boundary; not run.
- `engctl eos sync-validate homelab`: repository/EOS parity validation.

The command vocabulary is coherent for the submitted boundary. Full native coverage for all later stages is not proven; see `ZEUS-NATIVE-VERIFICATION-COVERAGE.md`.

