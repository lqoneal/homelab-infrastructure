# Section Boundary Mapping

| Source section | Boundary rule | Canonical destination | Result |
|---|---|---|---|
| Submission Metadata | inline labels until next peer heading | required metadata fields | PASS |
| Scope | `## Scope` through before next `##` peer | `mission.yaml.scope`; exact source in `source-wop.md` | PASS |
| Gates | `## Gates` through next recognized peer | `gates.yaml.gates` | PASS |
| Qualification Requirements | peer heading boundary | mission and roadmap projections | PASS |
| Completion Requirements | peer heading boundary | mission and roadmap projections | PASS |
| Transaction Identification and later sections | not consumed as preceding metadata | preserved in `source-wop.md` | PASS |
| Frontmatter | source preservation and explicit parsed labels | source copy plus canonical fields | PASS |

Nested headings are retained in the source copy and do not terminate their
parent metadata section. Peer headings never disappear into a prior field.
