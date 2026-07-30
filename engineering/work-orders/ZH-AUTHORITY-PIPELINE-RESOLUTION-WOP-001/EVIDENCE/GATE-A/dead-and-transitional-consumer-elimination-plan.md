# Gate A Dead and Transitional Consumer Elimination Plan

Date: 2026-07-29

Mission: `ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001`

Gate: `A`

Status: `IN_PROGRESS — CONSUMER_REDIRECTION_REQUIRED`

Nature: planning evidence only. This plan does not authorize or perform an
implementation, redirect, migration, compatibility layer, external-tree
permission change, or Gate B operation.

## Planning basis and boundaries

This plan reuses the Gate A inventory, semantic review, and architectural
reachability classification in `gate-a-inventory-report.md` and
`external-wop-inventory.json`. It does not repeat those investigations.

The classifications are:

| Consumer | Classification | Disposition objective |
|---|---|---|
| `scripts/lib/emp/oa02_lifecycle.py` | `DEAD CODE` | Complete retirement |
| `scripts/lib/emp/gate_approval.py` | `ACTIVE TRANSITIONAL` | Progressive replacement then retirement |
| `engineering/tests/zeus-operational-alpha/lib/pmct.py` | `ACTIVE TRANSITIONAL` | Narrow to remaining Progressive capability requirements |

No contradictory repository evidence was found. No consumer is
`ACTIVE AUTHORITATIVE`; therefore no compatibility adapter, migration layer,
or new authority model is permitted or proposed.

The external tree and its unique approvals, decisions, and verification
records remain historical evidence. Nothing in this plan makes them current
authority.

## Existing canonical owner map

| Retained responsibility | Current owner | Existing implementation | Canonical runtime record | Canonical receipt | Canonical verification |
|---|---|---|---|---|---|
| Progressive gate specification and active-gate lifecycle | Progressive OA package | `scripts/lib/emp/progressive_oa.py`; `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gate-specification.yaml` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json` | Active receipt selected by each gate's `acceptance_receipt` field | Gate-specific `runtime/evidence/OA-XX/VERIFIED` |
| Progressive gate verification | Gate-specific Progressive verifier | `scripts/lib/emp/oa01_gate_verification.py` through the implemented `oa05_gate_verification.py`; later gates retain their package verification contract until implemented | `runtime/evidence/OA-XX/VERIFICATION.json` | `runtime/decisions/OA-XX/accepted-*.json` selected by state; preserved legacy flat JSON receipts remain historical | `runtime/evidence/OA-XX/VERIFIED` |
| Progressive acceptance, rejection, replay, receipt validation, and advancement | Progressive OA | `progressive_oa.decide()`, `verify_receipt()`, and `controller()` | Progressive `runtime/state.json` | Progressive JSON decision under `runtime/decisions/OA-XX/` | `_marker_binding()` validates `VERIFIED` and `VERIFICATION.json` |
| Progressive read-only status and next action | Progressive OA | `progressive_oa.status()` and `next_action()` selected by `scripts/zeus` when the canonical state exists | Progressive `runtime/state.json` | Receipt pointer in state when the gate is accepted | Current gate state plus its canonical marker/decision binding |
| Controlled Mission Authority | Mission Contract plus Controlled Mission Authority | `scripts/lib/emp/controlled_mission_authority.py` | Resolved current authority observation; package admission and repository bindings | Canonical package admission receipt and predecessor Progressive gate receipt | `ControlledMissionAuthority.require()` checks |
| Mission eligibility | Mission eligibility owner | `scripts/lib/emp/mission_eligibility.py`; `zeus eligibility evaluate` | Caller-supplied staged candidate and current canonical mission inputs | No gate-approval receipt is created by eligibility evaluation | Deterministic eligibility result |
| Production agent registry and qualification records | Agent qualification owner | `scripts/lib/emp/agent_qualification.py` | `.zeus/runtime/agents/` and production agent registry projection | Qualification/revocation records owned by agent qualification | Qualification input checks; predecessor validation has the implementation gap recorded below |
| PMCT capability matrix, observation, run evidence, and capability-state ledger | PMCT contract and harness | `PMCT-CONTRACT.md`, `PMCT-CAPABILITY-MATRIX.yaml`, `lib/pmct.py` | `engineering/runtime/pmct/capability-state.yaml` and `engineering/runtime/pmct/runs/PMCT-*` | None; PMCT PASS is not operator acceptance | PMCT result, run manifest, artifact hashes, and `COMPLETE` marker |
| Mission initiation decision | EWI | `scripts/lib/eos/platform.sh`, work-initiation authorization-bundle resolution, and shadow/enforcement path | EWI-owned observation and initiation records | EWI decision record, not a Progressive gate receipt | EWI validation; none of the three consumers is an EWI input |
| Resolved execution authority | ARS/REAC owner | Existing authority-pipeline resolution contracts | Canonical REAC when produced and selected | REAC is not a Progressive gate receipt | REAC schema, integrity, freshness, and binding validation |

## Dead Consumer Retirement Plan

### Consumer: `scripts/lib/emp/oa02_lifecycle.py`

#### Current responsibilities

1. Calculate a legacy OA-02 pre-execution decision digest.
2. Resolve repository HEAD and the published authority baseline.
3. Resolve legacy OA-01 PMCT verification and acceptance through
   `GateApprovalService`.
4. Select a legacy OA-02 PMCT run.
5. inspect dispatcher state and production-agent qualification.
6. Derive legacy blockers, readiness, dispatch authorization, and next action.
7. Read a checksummed external OA-02 verification record.
8. Write or replay that external OA-02 verification record and checksum.
9. Project the legacy lifecycle into `CONDITIONALLY_ELIGIBLE`, `VERIFIED`,
   dispatch-ready, and dispatch-authorized states.

#### Remaining legitimate responsibilities

None remain in this module. The concepts that remain legitimate are already
owned elsewhere:

| Concept | Existing Progressive owner |
|---|---|
| OA-02 verification and marker validation | `oa02_gate_verification.py`; canonical OA-02 `VERIFICATION.json` and `VERIFIED` |
| OA-02 acceptance and replay | `progressive_oa.decide()` and `verify_receipt()`; canonical OA-02 decision receipt |
| Gate advancement and next action | Progressive `runtime/state.json`, `progressive_oa.controller()`, and `next_action()` |
| Controlled OA-02 authority | `ControlledMissionAuthority` and the Mission Contract |
| Mission eligibility after OA-05 | `mission_eligibility.py` |
| Dispatcher and agent observations | Their existing dispatcher and agent owners; not an OA-02 external verification projection |

#### Responsibilities to remove

Remove each behavior independently:

1. External `operator-verifications/OA-02.verification.json` discovery.
2. External SHA-256 sidecar validation.
3. External verification record creation.
4. External verification sidecar creation.
5. Legacy OA-01 gate-service prerequisite resolution.
6. Legacy OA-02 PMCT candidate selection.
7. Legacy decision-digest construction.
8. Legacy OA-02 state vocabulary projection.
9. Legacy dispatch authorization projection.
10. Legacy next-action selection.
11. `scripts/zeus` imports of `resolve_oa02` and `verify_oa02`.
12. Non-Progressive `verify OA-02` routing.
13. Legacy `authority_status()` OA-02 projection.
14. `scripts/lib/emp/next_action.py` import and conditional invocation.
15. Direct module tests that exist only to qualify this lifecycle.

#### Retirement sequence

1. Add characterization assertions showing that default `zeus status`,
   `next-action`, `verify OA-02`, gate receipt inspection, and resume select
   Progressive owners while the canonical Progressive state exists. No
   behavior change.
2. Remove the legacy OA-02 fields from the non-authoritative legacy status
   presentation or remove that unreachable presentation as one review unit.
   Verify the default Progressive status schema is byte-for-byte unaffected.
3. Remove the legacy `verify OA-02` branch and its imports from `scripts/zeus`.
   Verify Progressive OA-02 verification routing remains selected.
4. Remove `resolve_oa02` from `scripts/lib/emp/next_action.py`, then remove the
   legacy next-action path if it has no remaining caller.
5. Remove `oa02_lifecycle.py`.
6. Remove or rewrite only the tests that targeted the retired module.
7. Run the full dependency and external-tree scans before accepting the review
   unit.

#### Risk analysis

| Removal | Behavioral risk | Migration risk | Required verification | Rollback boundary |
|---|---|---|---|---|
| Legacy Zeus routing | An explicitly forced `ZEUS_PROGRESSIVE_OA=0` workflow loses OA-02 behavior | Hidden automation may still force legacy mode | Environment/config scan; command characterization; shell/service/process scan | Revert only the routing review unit; no state conversion |
| Legacy next-action projection | A legacy BETA diagnostic loses fields | A caller may parse undocumented fields | Search scripts/docs/services for field names; CLI snapshot tests | Revert next-action review unit |
| External verification read/write | Historical record may no longer be displayed by old tooling | None; the record must not migrate | Confirm canonical Progressive verification and receipt validation; external tree hash comparison | Revert module removal; never copy the record |
| Module and tests | An unscanned direct Python caller may fail import | Test coverage may have been mistaken for production need | Repository import scan, installed launcher scan, full regression | Restore module and its tests from the single review unit |

### Test impact

| Test disposition | Tests |
|---|---|
| Remove | `scripts/tests/test-zeus-oa02-lifecycle.py` tests that directly qualify the dead resolver |
| Rewrite | Legacy-mode sections of `scripts/tests/test-zeus-next-action.py` that assert the retired OA-02 projection |
| Convert to fixtures | Any retained negative test that needs a malformed or historical OA-02 record must create it under a temporary fixture root |
| Retain | Progressive OA-02 implementation, controlled-authority, gate-verification, receipt, replay, and cumulative regression tests |

## Transitional Consumer Narrowing Plan

### Consumer: `scripts/lib/emp/gate_approval.py`

#### Current responsibilities

1. Validate OA gate identifiers and PMCT completion markers.
2. Resolve configured repository, PMCT runtime, capability state, operator,
   and external WOP root.
3. Discover legacy flat and versioned text approval receipts.
4. Validate receipt SHA-256 sidecars and predecessor lineage.
5. Select PMCT PASS run candidates bound to authority publication, repository,
   HEAD, published baseline, and capability state.
6. Verify PMCT artifact manifests and the narrow capability-state
   reconciliation.
7. Validate the external WOP manifest.
8. Execute external resume and next-gate eligibility commands.
9. Construct a PMCT-qualified gate binding.
10. Validate legacy OA-01 carry-forward.
11. Project PMCT lifecycle values.
12. Read, validate, create, and failure-record external operator verification.
13. Match external approval receipts to a binding.
14. Execute the external approval persistence primitive.
15. Present legacy verification and approval CLI workflows.

#### Remaining legitimate responsibilities

The module itself retains no authoritative Progressive gate responsibility.
The underlying requirements that remain legitimate already have owners:

| Requirement | Existing owner and canonical records |
|---|---|
| Gate ID, active gate, and sequence | Progressive gate specification plus `progressive_oa.gate()` and `runtime/state.json` |
| Gate verification | Gate-specific Progressive verifier, `VERIFICATION.json`, and `VERIFIED` |
| Acceptance, rejection, immutable receipt, replay, supersedence, and advancement | `progressive_oa.decide()`, `verify_receipt()`, `controller()`, and `runtime/decisions/OA-XX/*.json` |
| Authority, repository, admission, predecessor, and active-gate binding | `ControlledMissionAuthority` plus the current Mission Contract and canonical Progressive receipts |
| PMCT run evidence and capability ledger | PMCT harness, PMCT run directory, artifacts manifest, completion marker, and capability state |
| Production-agent qualification records | `agent_qualification.py` and `.zeus/runtime/agents/` |

#### Responsibilities to remove

Remove each obsolete behavior separately:

1. Default external WOP selection.
2. Legacy flat text approval receipt discovery.
3. Versioned text approval receipt discovery.
4. Text receipt field parsing.
5. Receipt sidecar validation.
6. Text receipt predecessor-lineage validation.
7. External operator-verification path selection.
8. External operator-verification read and matching.
9. External operator-verification creation.
10. External operator-verification failure creation.
11. External WOP manifest validation.
12. External `resume-status` execution.
13. External `check-gate-eligibility` execution.
14. External `record-operator-approval` execution.
15. Legacy acceptance matching.
16. Legacy next-gate eligibility projection.
17. Legacy verification instruction presentation.
18. Legacy verification command.
19. Legacy approval command.
20. Legacy `accept`/`gate_decision` workflow.
21. Legacy OA-01 carry-forward workflow after Progressive receipt replay is
    confirmed as the only current behavior.
22. Legacy next-action dependency.
23. Legacy OA-02 lifecycle dependency.
24. Legacy PMCT approval-lifecycle dependency.

PMCT artifact validation and narrow capability-state validation must not be
silently deleted merely because they coexist in this module. Their remaining
use belongs to the PMCT owner and must be evaluated in the PMCT narrowing
review unit below.

#### Remaining command disposition

| Production command | Ultimate canonical input | Existing owner | Disposition or gap |
|---|---|---|---|
| `zeus status` | Progressive runtime state | `progressive_oa.status()` | Remove legacy gate-service projection |
| `zeus next-action` | Progressive runtime state and selected receipt | `progressive_oa.next_action()` | Remove legacy resolver path |
| `zeus verify OA-XX` | Progressive evidence, Mission Contract/controlled authority where required | Gate-specific Progressive verifier | Remove legacy verify branch |
| `zeus approve OA-XX --operator` | Progressive marker, evidence, state, and receipt history | `progressive_oa.decide()` | Remove legacy approval branch |
| `zeus decline OA-XX --operator` | Progressive marker, evidence, and state | `progressive_oa.decide()` | Retain current Progressive branch |
| `zeus gate receipt OA-XX` | Progressive state receipt pointer, marker, and evidence | `progressive_oa.verify_receipt()` | Retain |
| `zeus resume` | Progressive runtime state and accepted receipt | `progressive_oa.controller()` | Retain |
| Legacy `zeus accept` | None | Superseded by Progressive approve/decline | Remove command path; do not translate records |
| Legacy gate carry-forward commands | Progressive state and receipt replay | `progressive_oa` replay validation | Remove legacy command path after command-use scan |
| `zeus agent qualify/status/registry/revoke` | Agent records plus current Progressive predecessor state/evidence/receipts and Controlled Mission Authority at the applicable gate | `agent_qualification.py` for agent records; Progressive OA and Controlled Mission Authority for predecessors | **Repository implementation gap:** the current agent qualifier has no existing function that validates canonical Progressive predecessor bindings; do not design it in Gate A |
| EWI initiation | REAC, Mission Contract, admission, and EWI-owned observations | EWI/ARS owners | No gate-service input; no change |

#### Retirement sequence

1. Freeze the public behavior baseline with characterization tests for every
   command in the disposition table. This is test work only.
2. Remove legacy `accept`, legacy verify/approve fallbacks, and legacy
   carry-forward routing only after a repository/configuration scan proves
   they are not selected by current workflows.
3. Remove `next_action.py` and `oa02_lifecycle.py` gate-service call families
   in their own review units.
4. Separate PMCT-owned artifact/capability-state validation from legacy
   approval persistence only if current PMCT requirements still exercise it.
   This is a move within an existing owner, not a compatibility layer.
5. Resolve the agent-qualification predecessor-validation implementation gap
   in the implementation gate that owns that later Progressive capability.
   Do not delete its legacy dependency before the owning Progressive command
   has an integrity-valid existing-owner path.
6. Remove `gate_decision.py` after its command route and tests are gone.
7. Remove `gate_carry_forward.py` after Progressive replay tests cover the
   current receipt behavior and no command/configuration caller remains.
8. Remove `gate_approval.py` only after the import graph is zero.
9. Run full external reference, process, service, runtime, command, and
   regression verification.

#### Risk analysis

| Removal | Behavioral risk | Migration risk | Required verification | Rollback boundary |
|---|---|---|---|---|
| Legacy CLI branches | Undocumented forced-legacy callers fail | A caller might depend on text output | Command/config/service scan; CLI snapshots; default Progressive workflows | Revert one routing review unit |
| Text receipts and verifications | Historical audit tooling loses a reader | Importing them would create false authority | Preserve inventory/digests; verify canonical receipt commands; never mutate external tree | Restore read-only legacy code only; no record copy |
| PMCT binding helpers | Current capability runs could lose integrity checks | Logic might be removed before ownership is established | PMCT focused tests and run artifact validation | Revert PMCT extraction/removal review unit |
| Agent dependency | Agent qualification may accept without a valid predecessor or stop working | Premature deletion creates an authority gap | Agent positive/negative/replay tests plus canonical predecessor tamper tests | Keep old path fail-closed until the separately owned gap is resolved; do not adapter-wrap it |
| Carry-forward removal | Accepted historical gate behavior might regress | Progressive replay and legacy carry-forward are not identical | Progressive receipt replay, supersedence, state-coherence tests | Revert carry-forward command removal |
| Final module deletion | Missed imports cause startup failure | Broad import-time coupling in `scripts/zeus` | Import graph, `--help`, all command discovery, full tests | Restore final deletion commit only |

### Test impact

| Test disposition | Tests |
|---|---|
| Remove | Tests whose sole contract is legacy text receipt creation, external lifecycle command execution, legacy verification instruction UX, or legacy `accept` behavior |
| Rewrite | Agent qualification, PMCT prerequisite, and command-routing tests so they assert existing Progressive owners; only after the owning implementation gap is resolved |
| Convert to fixtures | Any retained parser/integrity negative test for a historical text receipt or WOP command must use a temporary fixture and must not imply current authority |
| Retain | Progressive decision, receipt integrity, replay, supersedence, state coherence, gate-specific verification, Controlled Mission Authority, and agent record integrity tests |

### Consumer: `engineering/tests/zeus-operational-alpha/lib/pmct.py`

#### Current responsibilities

1. Load and validate the 30-gate PMCT capability matrix.
2. Discover required Zeus command surfaces.
3. Observe repository, Git, authority, dispatcher, agent, PMCT, and next-action
   state.
4. Read the published baseline.
5. Discover legacy OA-01 verification through the external WOP.
6. Classify PASS, FAIL, BLOCKED, and NOT_READY.
7. Validate predecessor status and legacy OA-01 acceptance.
8. Evaluate gate-specific cumulative assertions.
9. Persist PMCT run evidence, manifests, hashes, reports, and completion
   marker.
10. Reconcile the PMCT capability-state ledger.
11. List, inspect, show, run, and report PMCT results.
12. Emit the fixed PMCT machine-readable result fields.

#### Remaining legitimate responsibilities

| Responsibility | Existing owner and canonical record |
|---|---|
| Matrix validation and cumulative gate selection | PMCT contract/harness and `PMCT-CAPABILITY-MATRIX.yaml` |
| Command discovery and capability observation | PMCT harness observing the repository-authoritative Zeus interface |
| Result vocabulary and deterministic assertion model | `PMCT-CONTRACT.md` and harness |
| Run evidence, manifest, hash, report, and completion marker | `engineering/runtime/pmct/runs/PMCT-*` |
| Capability-state reconciliation | `engineering/runtime/pmct/capability-state.yaml` |
| Exact-run list/inspect/report | PMCT harness and PMCT run directories |
| Current predecessor gate status | Progressive `runtime/state.json`, selected Progressive receipt, and marker verification |

#### Responsibilities to remove

1. External WOP default.
2. External OA-01 verification-file presence check.
3. Legacy `GateApprovalService` OA-01 binding.
4. Legacy `GateApprovalService` OA-01 acceptance check.
5. Legacy `GateApprovalService` OA-02 assertion check.
6. Legacy OA-01 verification readiness vocabulary when used as a current
   Progressive gate prerequisite.
7. Legacy next-action assertions tied to the superseded resolver.
8. Legacy dispatcher/OA-02 pre-execution assertions when not required by the
   current Progressive gate specification.
9. Tests that patch or construct the legacy gate service solely for those
   assertions.

#### Remaining PMCT command disposition

| Command | Ultimate canonical input | Disposition |
|---|---|---|
| `pmct list` | PMCT run directories | Retain |
| `pmct inspect [RUN]` | PMCT run evidence and current repository observations | Retain; must not read external WOP |
| `pmct show OA-XX` | PMCT matrix and contract | Retain |
| `pmct report RUN` | Exact PMCT run evidence | Retain |
| `pmct report OA-XX` | PMCT run evidence; documented interactive convenience only | Retain only if still required by PMCT contract |
| `pmct run OA-XX` | PMCT matrix, authoritative Zeus command surface, Progressive runtime state/evidence/receipts for predecessor gates, Mission Contract/Controlled Mission Authority where the selected gate requires it | Narrow and retain only if a current Progressive verification or controlled workflow calls it |
| PMCT use by EWI | REAC/EWI inputs, if ever specified by the EWI owner | No current caller or owner; do not add one |

The harness has a repository implementation gap: it does not currently
validate predecessor gates through the canonical Progressive state, marker,
and selected receipt. The owners and records exist, but no existing PMCT
function performs that validation. Record the gap; do not design a
replacement in Gate A.

#### Narrowing sequence

1. Characterize matrix validation, cumulative selection, result vocabulary,
   exact-run resolution, evidence sealing, and capability-state reconciliation
   independently of gate approval.
2. Identify current Progressive verification modules or controlled workflow
   commands that invoke `pmct run`. If the caller set is zero, record that
   result before changing the installed executable.
3. Remove external OA-01/OA-02 lifecycle observation from read-only inspect
   output and verify retained output fields.
4. Remove legacy gate-service prerequisite checks from `classify()` and
   OA-02 assertions only in the same implementation gate that resolves the
   canonical predecessor-validation gap.
5. Remove legacy next-action and dispatcher assertions not required by the
   current Progressive gate contract.
6. Delete or fixture-convert the corresponding tests.
7. If `pmct run` has no current production caller, remove its installed
   production launcher and retain the harness only as a repository test tool.
   If a current caller exists, retain only the characterized PMCT-owned
   responsibilities and canonical inputs.
8. Rescan and run focused plus cumulative regressions.

#### Risk analysis

| Removal | Behavioral risk | Migration risk | Required verification | Rollback boundary |
|---|---|---|---|---|
| External verification projection | Inspect output changes | A parser may rely on stale fields | CLI output inventory and caller scan | Revert projection removal |
| Legacy predecessor check | Later gate could pass without accepted predecessors | Canonical receipt validation gap could be hidden | Negative missing/tampered/superseded receipt tests | Do not merge removal until gap is resolved; revert one review unit |
| OA-02 special assertions | Loss of dispatcher safety coverage | Coverage may belong to another gate | Map assertions to current gate specification; run dispatcher safety tests | Restore assertion review unit |
| Installed `pmct run` | Operator tooling disappears | Hidden shell automation may invoke launcher | PATH/install/config/service/process scan | Restore launcher only |
| Evidence writer narrowing | Run artifacts or capability state become incomplete | Historical schema consumers may break | Golden run manifest/hash/COMPLETE tests and state reconciliation tests | Revert writer review unit; never rewrite old runs |

### Test impact

| Test disposition | Tests |
|---|---|
| Remove | Legacy gate-service adapter assertions in `test-state-protection.py` after replacement ownership is established |
| Rewrite | State protection and prerequisite tests to canonical Progressive state, marker, and selected receipt after the recorded implementation gap is resolved |
| Convert to fixtures | Historical PMCT/approval mismatch cases that need legacy record shapes |
| Retain | `test-contract.py`, `test-cumulative-selection.py`, command discovery, evidence integrity, idempotency, result model, exact-run selection, safe runtime, and capability-state reconciliation tests that do not require legacy approval state |

## Dependency Elimination Matrix

| Dependency | Current consumers | Elimination action | Required predecessor | Completion proof |
|---|---|---|---|---|
| External OA-02 verification JSON and sidecar | `oa02_lifecycle.py` | Remove dead resolver and routing | Progressive route characterization | Zero repository reference; Progressive OA-02 regression PASS |
| External WOP root default | `gate_approval.py`, `pmct.py` | Retire gate service; narrow PMCT | Resolve agent and PMCT predecessor-validation gaps in their owning implementation gates | Zero production reference |
| External `record-operator-approval` | Gate service and one test copy | Remove production invocation; generate isolated fixture only if parser tests remain | Progressive receipt regression | Zero production and test reference |
| External `check-gate-eligibility` | Gate service and next-action test | Remove legacy command dependency; fixture only if a historical parser test remains | Progressive next-action/state tests | Zero production and test reference |
| External `resume-status` | Gate service | Remove legacy lifecycle check | Progressive controller/resume tests | Zero production reference |
| Legacy text approvals | Gate service, decision, carry-forward, agent qualification, PMCT | Remove current consumption; preserve external history | Canonical Progressive receipt validation for each retained caller | No current authority decision reads text receipts |
| Legacy PMCT-bound verification | Gate service, next-action, agent qualification, PMCT | Remove current consumption | Canonical Progressive marker/receipt predecessor validation where legitimate | Missing/tampered canonical evidence fails closed |
| Legacy OA-02 state projection | OA-02 resolver, next-action, PMCT, status | Remove | Progressive state/status/next-action | Schema and command regressions PASS |

## Verification Matrix

| Verification class | Command or inspection | Required result |
|---|---|---|
| Repository reference scan | Fixed-string `rg` for the exact external root across production, tests, configs, docs selected as executable inputs, and services | Zero production references and zero test references; historical evidence references remain classified and excluded from executable counts |
| Import/dependency scan | `rg` for `oa02_lifecycle`, `GateApprovalService`, `gate_approval`, legacy `gate_decision`, and legacy carry-forward imports | Zero imports after each owner is retired; no dangling startup import |
| Environment/config scan | Search for `ZEUS_PROGRESSIVE_OA=0`, `ZEUS_GATE_WOP`, external path variables, shell profiles in scope, service units, cron, and repository automation | No production selection of legacy mode or external root |
| Runtime process scan | `/proc` cwd, executable, and open-file scan used by `inventory-external-wop` | Zero active users |
| Service scan | `/etc/systemd`, `/etc/cron.d`, and `/etc/crontab` scan used by inventory | Zero consumers |
| Command verification | `scripts/zeus --help`, `status`, `next-action`, gate show/objective/evidence/receipt, relevant verify/approve/decline/resume tests, and agent command tests | Progressive routing preserved; removed legacy commands absent or fail with documented unsupported-command behavior |
| PMCT command verification | list, inspect exact run, show, report exact run, and run only if retained | Retained commands use no external record and preserve artifact integrity |
| Progressive regression | OA-01 through current gate implementation, verification, receipt, replay, supersedence, recovery, and cumulative tests | PASS |
| EMP regression | Mission orchestration, admission, execution, eligibility, agent registry/qualification as applicable | PASS; no legacy gate receipt authority |
| Mission Contract/authority regression | Controlled Mission Authority positive, stale, missing, mismatch, and wrong-gate tests | PASS/fail closed as specified |
| EWI regression | Authorization-bundle, shadow/enforcement, and non-dispatching initiation tests | Unchanged and no new dependency |
| External integrity | Root mode/inode plus manifest and sidecar validation | Tree unchanged; mode remains `0755` |
| Full consumer inventory | Rerun `scripts/inventory-external-wop` to fresh Gate A evidence | `production_consumers=0`, `test_consumers=0`, `service_consumers=0`, `active_process_users=0` |

## Implementation Order

Each item is a separate review unit. Later implementation work must stop at
the first failed prerequisite.

1. Add non-mutating characterization tests for current Progressive command
   selection and existing canonical receipt/marker validation.
2. Convert the two direct external-path tests to isolated fixtures so tests
   stop executing or copying the external tree.
3. Retire dead `oa02_lifecycle.py` routing and then the module.
4. Remove superseded legacy status, next-action, verify, approve, accept, and
   carry-forward command routes in independently reviewable units.
5. Narrow PMCT observation away from external OA-01/OA-02 records while
   retaining its characterized matrix, evidence, and capability-state duties.
6. Resolve the PMCT canonical predecessor-validation implementation gap in
   the implementation gate that owns PMCT.
7. Resolve the agent-qualification canonical predecessor-validation
   implementation gap in the implementation gate that owns agent
   qualification.
8. Remove `gate_decision.py`, `gate_carry_forward.py`, and finally
   `gate_approval.py` when their import counts are zero.
9. Determine from the post-narrowing caller scan whether `pmct run` remains a
   production command. Remove its launcher if it is test-only; otherwise
   retain only its PMCT-owned canonical behavior.
10. Run focused, cumulative, full repository, external consumer, process,
    service, and mode/integrity verification.
11. Update Gate A evidence with actual implementation results. Only verified
    zero consumers and zero active users may support a later freeze request.

## Risk Register

| ID | Risk | Likelihood / impact | Control | Stop condition |
|---|---|---|---|---|
| R1 | Hidden forced-legacy caller | Medium / high | Environment, config, service, cron, docs-as-command, and process scans | Any current caller of `ZEUS_PROGRESSIVE_OA=0` |
| R2 | Agent qualification loses predecessor authority validation | High / critical | Keep fail-closed until canonical predecessor tests exist | No existing owner path for required binding |
| R3 | PMCT later-gate prerequisite becomes permissive | High / critical | Missing/tampered/superseded Progressive receipt negative tests | Removal precedes canonical validation |
| R4 | Historical evidence is imported as current authority | Low / critical | No copy/migration; preserve external manifest | Any proposed record translation |
| R5 | CLI output consumer breaks | Medium / medium | Call-site and output-field scan; snapshot tests | Unclassified parser or automation |
| R6 | PMCT integrity coverage is lost with gate service | Medium / high | Characterize artifact and state checks before separation | No retained owner for a required check |
| R7 | Test fixture accidentally reads live repository/WOP state | Medium / high | Temporary roots, explicit environment isolation, negative path assertion | Exact external or canonical live WOP used by test |
| R8 | External tree changes during planning/implementation | Low / critical | Mode/inode/manifest comparison before and after | Any digest, mode, inode, or file change |
| R9 | Gate B work begins prematurely | Low / high | Keep WOP active gate A and limit evidence path | Any Gate B artifact or state transition |

## Rollback Matrix

| Review unit | Rollback action | Preserved boundary |
|---|---|---|
| Test fixture conversion | Revert test-only change | No production state or external record touched |
| Dead OA-02 routing removal | Revert routing change | Progressive state/evidence/receipts unchanged |
| Dead module deletion | Restore module and imports | No record migration or schema change |
| Legacy CLI route removal | Restore only the command route | External tree remains read-only historical input pending later retirement |
| PMCT narrowing | Restore the prior PMCT functions and tests | Existing PMCT runs are never rewritten |
| Agent predecessor correction | Revert agent-owned review unit | Agent records remain append-only; no inferred qualification |
| Gate decision/carry-forward removal | Restore the individual module/route | Progressive decisions and historical receipts unchanged |
| Gate approval final deletion | Restore deletion review unit | No compatibility directory or copied external evidence exists |
| PMCT launcher removal | Restore launcher mapping | Harness records and contract unchanged |
| Scan/evidence update | Withdraw the new evidence artifact | External and runtime state unchanged |

Rollback must never copy an external approval or verification into the
canonical package, restore external records as current authority, weaken
fail-closed behavior, or begin Gate B.

## Gate A completion recommendation

Planning exit criteria are satisfied:

1. Every remaining consumer has a bounded retirement or narrowing plan.
2. Every retained responsibility has an existing canonical owner, except the
   two explicitly recorded implementation gaps for PMCT and agent
   predecessor validation.
3. Every obsolete responsibility is listed individually.
4. Every implementation review unit has verification and rollback.
5. Implementation order, dependency eliminations, risks, tests, commands, and
   zero-reference checks are documented.
6. No compatibility adapter, migration layer, new authority model, or
   Progressive/Mission Contract redesign is proposed.
7. No production code was modified by this planning work.

Recommendation: mark the Gate A **planning activity** complete, but do not
complete Gate A itself. Gate A must remain
`IN_PROGRESS — CONSUMER_REDIRECTION_REQUIRED` until later authorized
implementation removes the references and fresh evidence proves zero
production consumers, zero test consumers, zero service consumers, and zero
active users. Do not request an external-tree freeze and do not begin Gate B.
