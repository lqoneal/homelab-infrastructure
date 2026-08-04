# VALIDATE_WOP Failure Trace

Trace: Markdown/DOCX source -> `extract` -> `validate_source` -> package `mission.yaml` -> Stage 1 receipt-backed resolution -> `MissionExecutionRuntime._execute_gate(VALIDATE_WOP)` -> `AdmissionController`.

The first failing point for the protected submission was final admission validation, where the projected WOP lacked `approval.authorized_lifecycle_state`, the execution authority references, and the required sections. The source extractor accepted only legacy scalar metadata and the package generator then dropped the canonical nested contract.

New source validation reports every missing canonical field before submission; the protected package is resolved through an in-memory, receipt-backed projection so its immutable tree digest is not changed.
