# Subsystem Implementation Work Packages

All packages are implementation-ready plans only; execution requires separate
authorization.

| Package | Objective and boundary | Dependencies | Deliverables and acceptance | Verification |
| --- | --- | --- | --- | --- |
| EMP | consume authoritative mission/planning projections; do not own authority | metadata/API, interfaces | planning integration; one-owner boundaries | interface suite |
| Zeus | resolve and expose canonical verification interfaces; no alternate authority path | metadata/API, qualification | stable `zeus` read-only contract mapping | capability/interface suites |
| EOS | consume repository projections without becoming authoritative | synchronization engine | directional projection and recovery behavior | synchronization suite |
| EENS | emit synchronization and qualification discrepancies as events | interfaces, EOS | attributable event contract | interface and capability suites |
| Metadata Engine | resolve, version, validate, migrate authoritative EMM facts | baseline, owner directory | canonical resolver, schemas, migration boundary | metadata suite |
| Documentation Generator | deterministically generate derived artifacts | metadata engine | reproducible projection pipeline | generated-artifact suite |
| Qualification Engine | execute validation and retain attributable evidence | metadata, generator | repeatable qualification pipeline | qualification suite |
| Engineering Information API | expose versioned logical metadata, not document parsing | metadata engine | stable request/response/error contract | API/interface suites |
| Synchronization Engine | execute directional, idempotent derived projections | metadata, owner directory | checkpoints, reconciliation, recovery semantics | synchronization suite |
| Conformance Framework | run prescribed fixtures and report evidence | all prior contracts | fixture registry and pass/fail reporting | end-to-end suite |

Every package shall declare its baseline locator, input metadata, output owner,
interface version, fixtures, evidence retention, and rollback/recovery plan
before implementation begins.
