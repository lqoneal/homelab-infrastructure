# CLI Consistency Report

`scripts/zeus mission admissions ZDCL-02 --json` is not a supported command;
the published parser rejects `admissions`. Repository-controlled
documentation does not require that command. Existing projections are
available through the canonical mission status, authority, contract, and
snapshot views.

No new operator command was added. The corrective adds readiness to the
existing ZDCL-02 projection and preserves the operator contract:

```text
scripts/zeus submit <wop>
scripts/zeus resume <mission>
```
