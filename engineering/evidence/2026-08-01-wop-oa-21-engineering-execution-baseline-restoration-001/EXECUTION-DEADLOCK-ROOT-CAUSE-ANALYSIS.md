# Execution Deadlock Root Cause Analysis

The deadlock was introduced by convergence-runtime routing in `scripts/zeus`
at commit `5decaed`. `zeus verify` for gates outside the already-qualified
progressive range rejected requests without `--wop`, and `execute-mission`
rejected start/resume requests without a convergence binding.

This made an unfinished engineering platform a prerequisite for the next
Operational Alpha capability. The restoration makes convergence explicit:
passing `--wop` still selects and validates convergence authority; omitting it
uses the established Operational Alpha admission/dispatch path.
