# Future Knowledge Audit Framework

Status: BETA-04 normative planning specification
Owner: Engineering Governance
Canonical source: controlled documentation and declared authority owners

## Classification and ownership matrix

| Artifact | Classification | Canonical source | Owner | Lifecycle | Maintenance | CAGF suitability |
| --- | --- | --- | --- | --- | --- | --- |
| Mission contract | Normative | Mission Contract authority | Engineering Governance | Controlled | Manual | No; source |
| Mission Knowledge Model | Canonical | MKM | EMP / Governance | Operational | Manual | No; source |
| Capability Registry | Canonical | Capability Registry | Governance | Operational | Manual | No; source |
| EMM bindings | Canonical | EMM | Engineering Governance | Operational | Manual | No; source |
| PMCT and gate semantics | Normative | PMCT / gate authority | Qualification authority | Controlled | Manual | No; source |
| WOP package manifest | Normative / Historical Evidence | Published WOP | Engineering Governance | Immutable | Manual at publication | No; evidence |
| EOS state | Runtime State | EOS | EOS | Operational | Runtime | No; source |
| Submission record | Runtime State | EMP/Zeus submission authority | Zeus | Operational | Runtime | No; source |
| Admission record | Runtime State | Zeus admission authority | Zeus | Operational | Runtime | No; source |
| Execution record | Runtime State | Zeus / qualified agent | Zeus | Operational | Runtime | No; source |
| Mission projection | Projection | Canonical resolver | Zeus | Derived | Generated/read-only | Yes |
| Queue projection | Projection | Canonical mission state | EMP/Zeus | Derived | Generated/read-only | Yes |
| Roadmap view | Projection | MKM and roadmap authority | EMP/Zeus | Derived | Generated/read-only | Yes |
| Controller JSON/human output | Projection | Shared projection object | Zeus | Derived | Generated/read-only | Yes |
| Qualification report | Historical Evidence | Qualification authority | Engineering Governance | Immutable | Manual | No; evidence |
| Recommendation register | Planning | Engineering Governance | Engineering Governance | Controlled | Manual | Candidate input |
| Operation Beta roadmap | Planning | Operation Beta authority | EMP/Governance | Controlled | Manual | Candidate input |
| BETA-04 activation record | Normative / Canonical | Published authority chain | Engineering Governance | Active | Manual publication | No; source |
| Zeus runtime root selection | Runtime State | Operator configuration | Zeus runtime | Operational | Runtime | No; source |

## Audit rules

Every significant artifact shall declare classification, owner, authoritative source, lifecycle, maintenance method, and dependencies. A proposed generated artifact shall also declare stable inputs, digest rules, generator ownership, validation, and stale-source behavior. CAGF shall generate projections only; canonical and historical records remain controlled sources.
