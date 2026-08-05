# Operand Capture

The first live failing comparison selected the wrong receipt-backed transaction because no explicit Stage 1 identifier was supplied. The corrected capture is:

```text
requested execution:                  ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806
incorrectly selected Stage 1 ID:      ZEUS-DEVELOPMENT-530cda01-7883-57cb-a67e-c8dc4bc010dc
canonical Stage 1 instance_id:         ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806
dispatch receipt instance_id:          ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806
provider transaction_id:               ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806
registration_id:                       EMM-DEV-21fbb4d8027dadc133d0cdab
admission_id:                          EMM-DEV-ADMISSION-21fbb4d8027dadc133d0cdab
execution receipt execution_id:        absent
```

A non-canonical requested value now fails with all operands included in the diagnostic; it cannot be silently accepted or substituted.
