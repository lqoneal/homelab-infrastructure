# Resume Digest Trace

`execute-mission resume` dispatches through `scripts/zeus`, resolves the
receipt-backed Stage 1 transaction, follows admission supersession lineage, and
then invokes `MissionExecutionRuntime.resume`. The failure occurred before
runtime execution, in `admission_supersession.py` while validating the
predecessor/successor package binding.

The corrected flow derives the immutable Stage 1 package digest first, checks
its package/registration/dispatch receipt lineage, then validates each
admission package-binding field before returning the terminal successor.
