# Semantic Validation Output Analysis

The validator correctly emits `FAIL:` diagnostics for an intentionally incomplete temporary Roadmap. The unittest previously allowed those direct helper prints to escape, creating ambiguity even though the test passed. The test now captures the validator output, retains fail-closed assertions, and emits four explicit `EXPECTED_NEGATIVE_FIXTURE_FINDING:` records.

No controlled-document rule was changed.
