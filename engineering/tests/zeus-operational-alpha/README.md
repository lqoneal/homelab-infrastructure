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

Normal execution is read-only. Runtime evidence is stored beneath
`engineering/runtime/pmct/runs/` and ignored by Git. Controlled capability
state remains at `engineering/runtime/pmct/capability-state.yaml`.

The initial overall state is `NOT_READY`; no historical implementation result
has been converted into a PMCT `PASS`.
