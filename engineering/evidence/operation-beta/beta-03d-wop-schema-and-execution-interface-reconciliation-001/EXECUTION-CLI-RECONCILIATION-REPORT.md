# Execution CLI Reconciliation Report

`status`, `resume`, `suspend`, and `cancel` now resolve one active execution
when `--execution-id` is omitted. Zero active executions fail closed with the
start/ID requirement. Multiple active executions fail closed and list the
valid IDs. Explicit IDs remain supported and are required to disambiguate.

The existing execution record is projected into Beta mission, queue, and
next-action views with its admission ID, execution ID, current gate, wait
category, current canonical validation result, and resume action.

Status is observational and returns success while reporting a waiting state;
resume still returns a nonzero result if execution remains blocked.
