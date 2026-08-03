# Metadata Ownership Matrix

| Owner | Fields owned | Zeus relationship |
|---|---|---|
| Engineering Governance | authority, approval, acceptance, publication disposition | Zeus verifies and reports |
| EMM/Metadata Engine | registered entities, revisions, resolution receipts | Zeus consumes exact receipts |
| SPEC-0008/PROC-0004 | ETP model and resolved manifest | Zeus consumes frozen result |
| EOS | repository identity, baseline, freshness, synchronization | Zeus preflights; no mutation here |
| EENS | lifecycle event append and delivery | Zeus emits/consumes contracts |
| EMP/Operation Beta | mission, roadmap, coordination state | Zeus projects; no duplicate mission source |
| Execution Interface | semantic routing and existing lifecycle owners | Zeus routes to owners |
| Provider qualification service | capability and availability facts | Zeus selects read-only |
| Provider adapter | provider execution receipt | Zeus verifies; adapter cannot advance state |
| Zeus runtime | admission orchestration and derived lifecycle projection | Zeus owns orchestration, not Governance facts |
