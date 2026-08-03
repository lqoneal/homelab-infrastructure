# Root Cause Analysis

The legacy dispatcher treated an agent assignment as sufficient evidence for `DISPATCHED`. The object lacked transaction, package, provider, qualification, registry, plan, and authority-snapshot bindings. Zeus therefore exposed a receiptless state. The corrective validates the complete chain before dispatch and demotes invalid historical state through one reconciliation path.
