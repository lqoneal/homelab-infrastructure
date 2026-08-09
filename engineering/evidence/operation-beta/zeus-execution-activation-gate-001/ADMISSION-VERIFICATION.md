# Admission Verification

Canonical command:

```text
scripts/zeus admit <durable-submission-receipt> --wop engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md --json
```

Result: `PASS`

- Admission ID: `ADMISSION-264c5bc0-4812-54d5-8f03-353d0cd0a899`
- Admission state: `ADMISSION_COMPLETE`
- Admission receipt: `/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57/receipts/ADMISSION-264c5bc0-4812-54d5-8f03-353d0cd0a899.json`
- Admission receipt digest: `0cd92adf19f1d157be0458da26a0a00c3695d6b49791fc14dd6ff763418d7276`
- Transaction digest: `8d59ec5298b9fa6d48ea80ffcb1c295577540826dfedc25e10dc2640405b1fc5`
- Mission identity preserved: YES
- WOP identity preserved: YES
- Repository baseline: `7f77dfdc4eb98d7eb8cbcb4a837a6cf0b3505a5c`
- Execution created: NO

Exact replay returned `PASS` with `duplicate_admission=IDEMPOTENT` and the same
admission, package, contract, authority, receipt, and transaction digests.

Post-admission native mission resolution failed closed because the canonical
P3 verifier reported global artifact cardinality 2 in each P3 class. The two
sets are the preserved historical `MISSION-BETA-562F443E16C69401` admission
and this target admission.

