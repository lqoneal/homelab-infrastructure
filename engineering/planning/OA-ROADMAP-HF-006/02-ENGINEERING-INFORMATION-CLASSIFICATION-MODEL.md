# Engineering Information Classification Model

Status: `PROPOSED — NON-AUTHORITATIVE`

## Class definitions

| Classification | Meaning | Permitted writer | Example |
|---|---|---|---|
| Authoritative | primary engineering fact | declared fact owner | Governance Decision |
| Derived | reproducibly generated from declared sources | generator only | Gate Catalog matrix |
| Runtime | mutable operational state with lifecycle/retention policy | runtime owner | active attempt/checkpoint |
| Historical | immutable retained record of a prior fact/event | archival owner/sealer | acceptance receipt |

## Operational Alpha planning-package inventory

| Artifact | Classification | Authoritative source / owner | Synchronization source and direction |
|---|---|---|---|
| OA controlled roadmap objectives and gate packages | Authoritative | controlled roadmap owner | source → generated catalog/verification index |
| Governance Decision | Authoritative | Governance | source → Authority Record consumers |
| Authority Record | Authoritative | Governance | source → resolver, contract derivation, WOP/EWI consumers |
| Mission Contract | Authoritative | EMP | source → context, admission, verification views |
| repository/baseline observation | Historical | repository/baseline owner | observation → REAC and reports |
| REAC | Derived | resolver from declared source owners | sources → REAC → admission |
| Mission Inventory and eligibility snapshot | Authoritative | EMP | source → selector/dashboard |
| selection and EWI receipts | Historical | Zeus evaluator/EWI | receipt → lifecycle and verification views |
| immutable WOP | Authoritative | WOP publisher | source → admission/catalog views |
| WOP qualification binding | Historical | independent qualifier | record → WOP/admission/catalog views |
| execution event, checkpoint, and EOS state | Runtime | EENS / EOS respectively | source → replay/projection/health views |
| evidence manifest and qualification/acceptance records | Historical | sealer, qualifier, acceptance owner | record → catalog status/report |
| Project State and Work Registry | Authoritative | their respective owners | source → EMP/REAC/projections |
| HF-005 lifecycle state, transition, dependency, reachability, cycle, ownership matrices | Derived | generator from gate metadata and source contracts | metadata → generated analysis |
| HF-005 Gate Catalog authored intent | Authoritative | roadmap documentation owner | source → generated catalog sections |
| Gate Catalog generated sections and command index | Derived | generator | metadata/contracts → catalog |
| Human Verification Guide authored guidance | Authoritative | documentation owner | source → generated verification index |
| qualification reports and acceptance receipts | Historical | qualifier / acceptance owner | source → dashboards/status |
| capability matrix and engineering dashboards | Derived | generator | capability/gate metadata → views |
| EOS dashboard/health projection | Derived | EOS from its runtime state | EOS state → dashboard |
| archived superseded reports and snapshots | Historical | archival owner | retained without reverse synchronization |

Every new artifact must add a row before its first publication. A document may
contain authored and generated sections, but each section must declare its
classification and source metadata.
