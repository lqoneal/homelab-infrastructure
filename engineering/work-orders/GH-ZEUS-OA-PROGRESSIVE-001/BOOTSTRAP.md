# Progressive Zeus Operational Alpha Bootstrap

Package: `GH-ZEUS-OA-PROGRESSIVE-001`
WOP: `WOP-8e6c4ab8-4c85-5d6c-9c90-10b8814bdf99`
Admission: the integrity-bound JSON record in `admission/` (`ACCEPTED`)

This is the authoritative entry document. It supersedes
`GH-ZEUS-OA-CERTIFICATION-001` for future OA execution but preserves that
package, its admission receipt, PMCT evidence, and all earlier OA records as
historical evidence. No earlier OA status is inherited.

## Preflight

Run:

```bash
cd /data/engineering/repositories/homelab
engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/verify-package.sh
scripts/engctl repository health
scripts/engctl eos sync-validate
scripts/engctl registry validate
scripts/zeus validate engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/submission.yaml --repository /data/engineering/repositories/homelab
scripts/zeus status
scripts/zeus next-action
```

Expected results are package integrity `PASS`, repository/EOS/registry
validation `PASS`, WOP validation JSON without failures, package status
`READY`, active gate `OA-01`, and next action `EXECUTE_OA-01`.

## Execution

Invoke `scripts/zeus resume` under the admitted WOP. The controller resolves
the first incomplete eligible gate and never runs more than that gate. Follow
the active gate implementation procedure, validate its complete contract,
reconcile records, and generate its operator package. The controller stops at
`AWAITING_OPERATOR_VERIFICATION`.

The operator follows the gate verification guide. Acceptance is recorded with
`scripts/zeus approve OA-XX --operator OPERATOR`, confirmed with
`scripts/zeus gate receipt OA-XX`, and consumed by `scripts/zeus resume`.
Rejection uses `scripts/zeus decline OA-XX --operator OPERATOR`.

Failure, rejection, stale authority, invalid evidence, conflict, or
interruption stops fail closed. Use `RECOVERY.md` and create a bounded record
from `templates/corrective-work.yaml`; neither record authorizes corrective
implementation. OA-30 ends at declaration preparation. Operational Alpha
declaration and baseline freeze require separate authority.
