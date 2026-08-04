# CLI to Runtime Trace

Authority was resolved from the published Operational Alpha chain recorded by `.zeus/runtime/authority/active-publication.json` (publication `AUTHORITY-PUBLICATION-583fe064-eeaa-487b-b12f-48d3548ceec2`), not from this session.

`execute-mission` dispatches in `scripts/zeus`, constructs the admission and execution stores, then invokes `stage1_execution_resolution.resolve` before `resolve_execution_id`, `AdmissionStateStore.load`, or `ExecutionStateStore.load`. The resolver validates the receipt-backed Stage 1 record and atomically installs both projections before the requested action continues.

The trace was qualified with disposable Stage 1, admission, and execution directories. Repeated resolution returned the same identities and did not rewrite either projection.
