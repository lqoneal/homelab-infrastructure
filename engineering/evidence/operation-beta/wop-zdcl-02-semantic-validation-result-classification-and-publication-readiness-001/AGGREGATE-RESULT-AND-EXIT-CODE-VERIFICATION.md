# Aggregate Result and Exit Code Verification

The bounded aggregate suite completed 36 tests with `OK` and exit code 0. The real invalid semantic fixture invoked through `validate_controlled_documents.py` returned nonzero. Thus expected negative evidence does not fail the aggregate suite, while actual validation failure remains fail-closed.
