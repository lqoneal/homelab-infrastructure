# Validator Consolidation Report

`wop_admission.py` is the shared submission/execution validator. The execution
gate calls it directly; semantic identity and optional-date rules are defined
in `wop_schema.py`. The JSON admission schema mirrors those rules. The legacy
offline WorkPackage contract remains isolated to its UUID-based historical
contract and fixtures.
