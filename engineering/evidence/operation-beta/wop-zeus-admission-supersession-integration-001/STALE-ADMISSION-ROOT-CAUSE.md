# Stale Admission Root Cause

The first stale-admission failure is `MissionExecutionRuntime._load_admission`: it compares `admission.artifacts.repository_baseline` with current `HEAD` and raises `stale admission cannot authorize execution` before execution launch. The previous Stage 1 resolver hydrated the predecessor projection but had no baseline-reconciliation path.
