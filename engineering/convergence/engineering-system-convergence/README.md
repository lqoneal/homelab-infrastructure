# Engineering System Convergence

This directory is the stable repository-authoritative root for program
`ENGINEERING-SYSTEM-CONVERGENCE` and roadmap `ESC-ROADMAP-001`. It is
self-contained for planning position and evidence discovery; conversational
history and volatile provider/session identifiers are not inputs.

## Authority and records

`roadmap.yaml` owns roadmap identity, sequence, gate locators, repository
baseline, and the reference-only preservation binding. Each gate's `GATE.yaml`
owns its executable definition. `STATE.yaml` is the only gate-position record.
Completed gates require a matching terminal `RESULT.yaml` and referenced
evidence; result-file presence alone never establishes completion.

`PROJ-0001` carries the project resume binding to this roadmap. EMM behavior is
implemented by the read-only convergence resolver: `binding-manifest.yaml`
binds the roadmap, Project State, gate definitions, and completed results by
SHA-256. PROC-0006 remains the qualification owner. This roadmap is planning
authority and does not itself grant implementation, publication, provider,
EOS synchronization, or other execution authority.

Any missing, malformed, unknown, overlapping, digest-drifted, or contradictory
roadmap/state/gate/result/evidence/Project-State input fails closed. The
resolver never chooses the newest file and never mutates state.

## Review and resume

From the repository root:

```text
engctl roadmap validate
engctl roadmap status
engctl roadmap show
engctl roadmap gate C02
engctl roadmap results
engctl resume
```

`engctl resume` renders the validated convergence context before the broader
legacy Engineering Work Initiation, EOS, registry, and mission views. Its
verification path is read-only: detected EOS/runtime drift is reported and is
not repaired.

## Recording gate results

Execute only the current gate and only within its `GATE.yaml` scope. Put
detailed artifacts under its `evidence/` path and write the executive result to
its fixed `RESULT.yaml` path using `schemas/result.schema.yaml`. A separately
authorized, reviewed transition must then update gate definitions, `STATE.yaml`,
the Project State binding when its current position changes, and EMM digests as
one consistency boundary. Never mark a gate complete from artifact presence.

Findings, convergence decisions, and the final migration plan have stable
program locations under `findings/`, `decisions/`, and `final-plan/`. Their
README files define the future owning gates and prevent placeholder material
from being mistaken for an approved result.
