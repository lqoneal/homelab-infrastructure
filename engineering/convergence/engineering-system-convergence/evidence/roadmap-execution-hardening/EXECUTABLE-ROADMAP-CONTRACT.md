# Executable Roadmap Contract

The controlled normative contract is STD-0006; the evaluation sequence is
PROC-0009. The machine-readable implementation is:

- `schemas/roadmap.schema.yaml` — roadmap class and evaluation bindings;
- `schemas/gate-historical-v1.schema.yaml` — frozen C00-C02 validation
  contract selected by explicit provenance;
- `schemas/gate.schema.yaml` — gate type, playbook reference, and terminal
  semantics;
- `schemas/execution-playbook.schema.yaml` — discovery, inventory, safety,
  coverage, classification, artifact, result, review, transition,
  persistence, and cold-resume contract;
- `schemas/roadmap-evaluation.schema.yaml` — qualification result;
- `execution-playbooks.yaml` — shared contracts and C00-C20 gate parameters;
  and
- `scripts/lib/eos/convergence_roadmap.py` — generic live structural and
  execution-sufficiency evaluator.

The evaluator treats structural validity and execution sufficiency separately.
`PLANNING_ONLY` can remain structurally valid with `EXECUTABLE=NO`. Any
execution-significant missing or ambiguous contract causes
`NOT_EXECUTABLE`.

The roadmap is mixed-generation: C00/C01 are historical frozen, C02 is
activation-era frozen, and C03+ are prospective executable. The resolver uses
the provenance-selected schema and reports STD-0006 as `NOT_APPLICABLE` for
C00-C02. `ESC-ROADMAP-001` remains the active temporary queue; Zeus staging is
not yet active as queue authority.
