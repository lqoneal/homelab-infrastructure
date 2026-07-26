# Zeus Progressive Manual Capability Test

The PMCT is the repository-controlled manual acceptance system for the locked
Zeus Operational Alpha sequence. It tests observable behavior through the
authoritative operator interface and produces an integrity-verifiable evidence
package. Implementation, documentation, schemas, fixtures, or unit tests never
independently satisfy a capability gate.

Start here:

```bash
engineering/tests/zeus-operational-alpha/bin/pmct inspect
engineering/tests/zeus-operational-alpha/bin/pmct list
engineering/tests/zeus-operational-alpha/bin/pmct show OA-01
engineering/tests/zeus-operational-alpha/bin/pmct run OA-01
engineering/tests/zeus-operational-alpha/bin/pmct report OA-01
```

For reproducible evidence review, use the exact returned run identifier with
`pmct inspect <PMCT-RUN-ID>` and `pmct report <PMCT-RUN-ID>`. Gate-based report
selection is a latest-run convenience only.

Normal execution preserves authoritative engineering, repository, and
operational decision state. Runtime evidence is stored beneath
`engineering/runtime/pmct/runs/` and ignored by Git. Explicitly documented,
bounded, non-authoritative presentation telemetry may advance. Controlled
capability state remains at `engineering/runtime/pmct/capability-state.yaml`.

The overall state remains `NOT_READY`. OA-01 has a P2-021 Codex demonstration
result of `PASS`, but independent operator verification is pending and
operator acceptance is not recorded. OA-01 gate status is
`AWAITING_OPERATOR_VERIFICATION`; OA-02 is blocked pending the required
operator acceptance. No historical implementation result was inferred as
operator acceptance.
