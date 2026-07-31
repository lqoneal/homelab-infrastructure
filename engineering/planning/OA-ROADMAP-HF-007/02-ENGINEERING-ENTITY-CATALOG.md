# Engineering Entity Catalog

Status: `PROPOSED — NON-AUTHORITATIVE`

| Entity | Identifier / purpose | Owner | Lifecycle / persistence | Class | Relationships |
|---|---|---|---|---|---|
| Governance Decision | `governance_decision_id`; bounded decision | Governance | decided→superseded/revoked; immutable | AUTHORITATIVE | enables Authority Record |
| Authority Record | `authority_record_id`; scope/validity | Governance | issued→effective/not-effective→revoked; immutable | AUTHORITATIVE | derives Contract; EWI/WOP input |
| Repository Identity | `repository_id`; repository fact | repository owner | registered→retired; immutable | AUTHORITATIVE | identifies baseline |
| Repository Baseline | `baseline_id`; exact boundary | baseline owner | observed→qualified→superseded; retained | HISTORICAL | REAC/admission input |
| Mission | `mission_id`; bounded work | EMP | staged→classified→selected→closed; versioned | AUTHORITATIVE | inventory/contract/selection |
| Mission Contract | `contract_id`; derived mission facts | EMP | derived→active→superseded; immutable | AUTHORITATIVE | context/WOP/EWI input |
| Mission Inventory | `inventory_id`; planned set | EMP | assembled→sealed→superseded | AUTHORITATIVE | creates snapshot |
| Eligibility Snapshot | `snapshot_id`; frozen classification | EMP | generated→consumed→expired | AUTHORITATIVE | selection input |
| WOP | `wop_id`; execution package | WOP publisher | published→qualified→withdrawn/superseded | AUTHORITATIVE | admission input |
| Admission Record | `admission_id`; typed result | admission owner | evaluated→valid/invalid→expired | HISTORICAL | EWI input |
| EWI Result | `ewi_id`; terminal initiation result | Zeus EWI | evaluated→ALLOW/DENY/STOP→expired | HISTORICAL | attempt input |
| Execution Attempt | `attempt_id`; fenced instance | Zeus | reserved→running→paused/interrupted→terminal | RUNTIME | emits events/evidence |
| Event | `event_id`; ordered observation | EENS | append→retain | RUNTIME | replay/health/evidence |
| Evidence | `evidence_id`; bound proof | producer/sealer | declared→sealed→retained | HISTORICAL | qualification input |
| Qualification | `qualification_id`; independent result | qualifier | evaluated→pass/fail/not-ready | HISTORICAL | acceptance/correction |
| Acceptance | `acceptance_id`; explicit decision | acceptance owner | accepted/rejected→superseded | HISTORICAL | closeout input |
| Reconciliation | `reconciliation_id`; source-target result | source owner | pending→reconciled/dirty/blocked | RUNTIME | closeout/health input |
| Closeout | `closeout_id`; terminal record | Zeus / EMP projection | pending→closed/blocked; retained | HISTORICAL | representative qualification |
| Project State | `project_state_id`; project facts | Project State owner | versioned owner lifecycle | AUTHORITATIVE | EMP/REAC source |
| Engineering Artifact | `artifact_id`; document/report/matrix metadata | declared artifact owner | draft→published→archived | AUTHORITATIVE | projection target |
| Engineering Registry | `registry_id`; controlled index | registry owner | active→reconciled→archived | AUTHORITATIVE | discovery/generator input |
| Engineering Dashboard | `dashboard_id`; status view | generator owner | generated→stale→regenerated | DERIVED | consumes facts/receipts |

All entities inherit the EMM envelope. Entity-specific attributes and relationships are defined in files 03 and 04.
