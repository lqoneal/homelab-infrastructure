# T03 Consumer Impact Assessment

| Consumer | Impact |
| --- | --- |
| `scripts/lib/emp/next_action.py` | Existing `resolve_oa02` import and response keys remain supported. |
| legacy Zeus OA-02 verification branch | Existing `verify(repository, record_path)` and `(record, replay)` result remain supported; artifact is now explicitly a projection. |
| Progressive CLI and `progressive_oa` | No T03 routing or interface change. |
| T01 primitive consumers | No change. |
| T02 decision consumers | No change. |
| PMCT | No implementation change; capability-state remains an observational compatibility input. |
| Agent Qualification | No implementation change; effective registry remains an observational compatibility input. |

The OA-02 compatibility response retains its established operator fields,
including readiness, dispatcher, agent, blocking-condition, decision-digest,
authorization, dispatch, and next-action fields. Authority-valued OA-01 and
OA-02 lifecycle facts now originate in canonical Progressive projections.

No consumer is required to migrate during T03. New Progressive consumers
should use `ProgressiveLifecycleProjector` for lifecycle views and
`ProgressiveGateService` for canonical authority.
