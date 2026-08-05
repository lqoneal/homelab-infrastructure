# Authority-Digest Trace

`stage1_execution_resolution.resolve` calls `admission_supersession.resolve_for_resume`. The first failing comparison was the direct `value.get("authority_snapshot_digest")` check in `admission_supersession.py`, which produced `observed=None` for a valid projection. The path now resolves the immutable Stage 1 authority digest before lineage and execution-projection validation.

