# Projection Integrity Matrix

| Projection | Canonical input | Active-state rule | Historical rule | Parity |
| --- | --- | --- | --- | --- |
| mission explain | canonical mission projection | current admission and zero/one current execution | history fields only | same object |
| mission queue | canonical mission state | active missions and executions | history projection only | same object |
| next-action | mission readiness and projection | current authorized action | no historical inference | same object |
| roadmap | roadmap authority and MKM | progress context | completed work allowed as context | same object |
| operation status | Beta authority and projections | operation state | historical Alpha context separate | same object |
