# Runtime Migration Report

Recovery upgrades pre-recovery Stage 1 records to schema version 3 in place and records `CANONICAL_TRANSACTION_RECOVERY_V1`. Identity-bearing fields and receipt payloads are unchanged. Migration is atomic through the existing state store.
