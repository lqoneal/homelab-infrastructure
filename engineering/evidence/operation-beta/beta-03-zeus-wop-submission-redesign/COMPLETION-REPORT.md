# BETA-03 Completion Report

## Result

The Zeus submission workflow now has one mission-oriented operator entry point
while retaining the existing package submission, admission, queue, and
execution authorities.

## How to Submit a Mission to Zeus

### 1. Submit by mission ID

```text
zeus mission submit ZDCL-01
```

This resolves the active Beta mission and searches the canonical WOP package
locations. At this baseline it fails closed because the approved ZDCL-01 WOP
package is not yet published.

### 2. Submit an existing WOP package

```text
zeus submit engineering/work-orders/WOP-ZDCL-01-FOUNDATION-001
```

The package must be a valid directory or `.tar.gz`/`.tgz` package accepted by
the existing Stage 1 validator.

### 3. Verify the queue entry

```text
zeus mission queue list
zeus mission queue show ZDCL-01
```

### 4. View readiness and blockers

```text
zeus mission readiness ZDCL-01
zeus mission blockers ZDCL-01
```

### 5. View the selected next mission

```text
zeus next-action
```

### 6. Admit, when submission is staged

```text
zeus admit-mission start --mode operational --mission ZDCL-01 --wop <WOP_ID> --submitter <SUBMITTER> --principal <PRINCIPAL>
```

Admission remains explicit and fail closed.

### 7. Start execution, after admission succeeds

```text
zeus execute-mission start --admission-id <ADMISSION_ID>
```

### 8. Resume after interruption

```text
zeus execute-mission resume --execution-id <EXECUTION_ID>
```

### 9. Check status

```text
zeus admit-mission status --admission-id <ADMISSION_ID>
zeus execute-mission status --execution-id <EXECUTION_ID>
```

### 10. Diagnose a rejected submission

```text
zeus show <MISSION_ID>
zeus explain rejection <REJECTION_RECORD>
```

The exact rejection evidence is authoritative. Missing authority, stale
baseline, invalid package, duplicate active submission, and unavailable
approval remain fail-closed.

## Boundaries

Submission never approves protected work, bypasses admission, executes a
blocked mission, mutates Production, or fabricates authority. Repeated
submission of identical package content is handled by the existing Stage 1
idempotent replay logic.
