# Admission Supersession Specification

Admissions are immutable records. A repository-baseline change does not
rewrite the old admission; it creates a replacement identity with lineage:
prior admission, cancelled incompatible execution, supersession reason,
previous baseline, and replacement baseline. Historical records remain
available for audit, while only a fresh compatible admission may authorize
execution.
