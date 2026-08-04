# Source Operand Capture

The failing operand was `value.get("source_digest")` in
`admission_supersession.py`'s lineage loop. For the valid successor its value
was `None`, while the authoritative Stage 1 expected operand was:

```text
0b41100481802772007dfd28f41fee9a7c195d81f2e9c30f42799218c3a3da8f
```

The corrected diagnostic identifies the exact field when a present value
conflicts. An absent generic field no longer overrides a validated Stage 1
source binding.
