# Human/JSON Parity Report

Human and JSON lint invocations use the same `ValidationResult` and issue list.
For a valid fixture both classify PASS. For incomplete and malformed fixtures
both classify failure (exit 78); JSON exposes structured fields and human
output renders the same issues and corrective action. No renderer performs
independent validation.
