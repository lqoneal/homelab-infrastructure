# WOP Command Parsing Map

| Command | Canonical source path | Mutation |
|---|---|---|
| `wop validate` | `validate_source` | none |
| `wop lint` | `validate_source` then `lint_source` | none |
| `wop inspect` | `validate_source` plus projection | none |
| `wop explain` | `validate_source` plus explanation projection | none |
| package input | `validate_package` | none |

All source commands resolve through `scripts.lib.emp.wop_validation`; lint
receives `ValidationResult.metadata` before evaluating quality issues.
