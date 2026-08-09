# Test Results

| Verification | Result |
| --- | --- |
| Supersession/cardinality corrective | PASS, 20 tests |
| Publication transaction | PASS, 11 tests |
| Transaction cohort revalidation | PASS, 8 tests |
| Publication candidate authority | PASS, 9 tests |
| Publication cohort | PASS, 3 tests |
| Authorized publication transition/baseline authority | PASS, 12 tests |
| Postpublication lifecycle reconciliation | PASS, 6 tests |
| Postpublication verification routing | PASS, 4 tests |
| Repository projection | PASS, 9 tests |
| Mission verification controller | PASS, 5 tests |
| Controlled-document relationships | PASS, 3 tests |
| Controlled-document validator | PASS, 3,808 checks / 0 failures |
| Corrective sidecar schema | PASS |
| Zeus platform/WOP schema | PASS |
| Registry schema and YAML serialization | PASS, 87 objects |
| Python compileall | PASS |
| `git diff --check` | PASS |
| Repeated live mission status | PASS, stable current identity/action |
| Historical transaction/receipt hashes | PASS, byte-stable |

All tests use temporary repositories/runtimes where mutation is required. The
live acceptance checks are read-only.

Two unrelated pre-existing regression observations were retained without
weakening their guards: `test-authority-publication.py` rejects temporary test
targets at the repository-fixed runtime-pointer boundary (13 failures/errors of
23), and one semantic-validator unit test disagrees with the already-modified
generated/historical-domain classifier. The canonical controlled-document
validator itself passes all 3,808 checks. Neither failing test imports or
exercises the corrected publication lineage resolver.
