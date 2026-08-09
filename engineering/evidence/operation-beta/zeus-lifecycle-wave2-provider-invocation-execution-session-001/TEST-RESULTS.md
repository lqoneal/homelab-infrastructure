# Test Results

Passing focused results included P5-G2 dispatch, P5-G3 provider session,
P5-G4 provider invocation after projection-test reconciliation, P5-G5
execution-start foundation (except the candidate-scope assertion below),
provider-boundary, provider live-lineage, Wave 1 controller, and Wave 3
bounded monitoring/recovery coverage where applicable.

The first direct test attempt failed at import collection because the
repository requires `PYTHONPATH=.`; the supported rerun used that context.

Two pre-existing/historical suites remain classified rather than hidden:

* the P5-G5 candidate-scope assertion rejects the preserved unrelated dirty
  tree as outside its old publication candidate;
* the P5-G6 historical Beta execution fixture expects old gate/active-process
  values while current runtime classifies it as reconciled historical.

Neither failure concerns the target mission's provider invocation or
execution-session receipts, and no validator was weakened to suppress them.
