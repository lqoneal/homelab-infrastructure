# P3/P4 Qualification Discovery

The reported P4 `RC=2` was test discovery failure, not a P4 test failure.
The exact authoritative P4 corrective suite is:

```text
python3 scripts/tests/test-zeus-p4-g1-bootstrap-boundary.py
```

Result: 21 tests passed.

The matching files are:

- `test-zeus-p3-g1-mission-admission-boundary.py`
- `test-zeus-p3-mission-scoped-cardinality.py`
- `test-zeus-p4-g1-bootstrap-boundary.py`
- `test-zeus-p4-g3-runtime-discovery.py`

`test-zeus-p4-g3-runtime-discovery.py` is historical compatibility coverage;
its preserved Beta expectation is recorded in the prior P4 evidence and was
not changed by this corrective. It is not the P4 cardinality qualification
suite.
