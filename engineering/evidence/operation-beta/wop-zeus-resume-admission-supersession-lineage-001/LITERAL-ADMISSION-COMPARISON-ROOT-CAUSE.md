# Literal Admission Comparison Root Cause

The first failing comparison was the literal check in
`stage1_execution_resolution.resolve`:

```text
requested_admission_id != receipts.admission.admission_id
```

That compared the immutable Stage 1 predecessor
`EMM-DEV-ADMISSION-814361acbc225619ade3614a` directly with the execution's
current successor `EMM-DEV-ADMISSION-120e6eb0b34c6cadf46fd857d5e43bc4`,
without following `superseded_by`.
