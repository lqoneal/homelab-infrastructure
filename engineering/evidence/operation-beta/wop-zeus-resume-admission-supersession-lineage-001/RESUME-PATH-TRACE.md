# Resume Path Trace

`scripts/zeus` dispatches `execute-mission resume` through
`resolve_stage1_execution`, selects the execution projection, and calls
`MissionExecutionRuntime.resume`. Runtime `run` then loads the admission bound
to that execution before validating the WOP binding.

The canonical resolver now resolves receipt-backed Stage 1 admission lineage
before projection lookup and before runtime conflict handling. The resume path
accepts the predecessor alias or the current successor and passes the terminal
successor to runtime.
