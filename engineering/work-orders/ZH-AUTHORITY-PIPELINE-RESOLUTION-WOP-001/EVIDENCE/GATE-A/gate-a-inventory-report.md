# Gate A External OA WOP Inventory Report

Date: 2026-07-29

Status: `IN_PROGRESS — CONSUMER_REDIRECTION_REQUIRED`

## Identity and manifest

The external tree remains unchanged and writable by its owner:

`/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP`, mode `0755`, device
`2065`, inode `2362046`.

The canonical comparison target is
`engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001`.

The machine-readable inventory is `external-wop-inventory.json`, digest
recorded inside that file. It contains the complete path, size, mode, mtime,
and SHA-256 manifest for both trees and a file-by-file comparison.

| Observation | Result |
|---|---:|
| External files | 101 |
| Canonical files | 186 |
| Byte-identical cross-tree files | 0 |
| Same-name divergent files | 1 (`MANIFEST.sha256`) |
| External-only path/name records | 100 |
| Active process users | 0 |
| systemd/cron consumers | 0 |
| Production repository references | 4 |
| Test repository references | 2 |

The external package's root manifest and every discovered sidecar SHA-256 file
validated. Integrity does not establish current authority or equivalence to
the canonical package.

## Active writers and consumers

The `/proc` cwd/executable/open-file scan found no active process using the
external tree. `/etc/systemd`, `/etc/cron.d`, and `/etc/crontab` contain no
reference to it.

Repository tooling still depends on it:

| Consumer | Class | Dependency |
|---|---|---|
| `scripts/lib/emp/oa02_lifecycle.py` | production | default OA-02 verification record, two call sites |
| `scripts/lib/emp/gate_approval.py` | production | default external gate WOP root |
| `engineering/tests/zeus-operational-alpha/lib/pmct.py` | production qualification | default `ZEUS_GATE_WOP` |
| `scripts/tests/test-zeus-next-action.py` | test | expected external path |
| `scripts/tests/test-zeus-gate-approval.py` | test | invokes external approval tool |

No permission freeze is safe while those defaults remain. A freeze could make
approval/lifecycle tooling fail or, worse, encourage a bypass. Gate D must
redirect each production consumer to repository-authoritative records and
convert the tests to isolated fixtures before approval is requested.

## Semantic classification

The 100 external-only records are classified by role:

| Class | Content | Disposition |
|---|---|---|
| obsolete executable compatibility tree | bootstrap, handoff, WOP, README, three commands, one backup | preserve manifest; redirect consumers; do not execute; retirement candidate |
| obsolete derived gate projection | OA-02 through OA-30 README/STATUS pairs | external state says OA-02 blocked while canonical state has progressed through accepted OA-05; preserve as historical snapshot, never import as current state |
| unique historical operator evidence | OA-01 approvals and decision history with valid sidecars | preserve immutable; map identities against canonical receipts before archive/retirement; never substitute as current acceptance |
| unique legacy verification evidence | OA-01, OA-02, OA-19, OA-20, OA-21 verification records with valid sidecars | preserve immutable; OA-19–OA-21 are not eligible current-gate evidence and must not enter canonical active state |
| templates | two report/verification templates | non-authoritative compatibility material; retain only if historical recovery needs them |
| divergent package manifest | external `MANIFEST.sha256` | retain with external archive; it describes a different package and cannot replace the canonical manifest |

The external `WOP.md` identifies a legacy “Remaining Operational Alpha Gates”
package covering OA-02–OA-30. The canonical `immutable-wop.yaml` identifies
`WOP-8e6c4ab8-4c85-5d6c-9c90-10b8814bdf99` and the rebuilt progressive
mission. They are semantically different packages, not mirrors.

## Gate disposition

Gate A inventory evidence is complete enough to identify the freeze blocker,
but Gate A exit criteria are not met because production and test consumers
remain. No freeze approval is requested at this point.

Next safe operation: implement and verify consumer redirection in the canonical
repository, rescan for zero consumers and active writers, present the updated
evidence, and only then request operator approval for the exact read-only
permission change.

## Consumer-redirection semantic review

The 2026-07-29 redirection review inspected every identified consumer before
modification. No consumer was changed because the production replacement is
not yet semantically complete.

| Consumer | Required semantics | Canonical candidate | Disposition |
|---|---|---|---|
| `scripts/lib/emp/oa02_lifecycle.py` | Read and write the legacy pre-execution OA-02 decision-digest verification record, including its sidecar checksum | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFICATION.json`, `VERIFIED`, `runtime/decisions/OA-02/*.json`, and `runtime/state.json` | **BLOCKED**: these are authoritative Progressive OA verification, marker, acceptance, and lifecycle records, but their identity, schema, digest bindings, and accepted lifecycle semantics differ from the legacy pre-execution record. Substitution would reinterpret historical evidence and `verify()` has no canonical write target with the same contract. |
| `scripts/lib/emp/gate_approval.py` | Resolve PMCT-bound gate verification records, append-only text approval receipts with SHA-256 sidecars and predecessor lineage, validate a package manifest, and execute resume, eligibility, and approval primitives | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001` | **BLOCKED**: the canonical package has its own JSON `runtime/evidence`, `runtime/decisions`, and `runtime/state` lifecycle. It does not contain the legacy `operator-verifications`, `operator-approvals`, `bin/resume-status`, `bin/check-gate-eligibility`, or `bin/record-operator-approval` contract. Merely changing the default root would fail at runtime and would conflate two incompatible lifecycle models. |
| `engineering/tests/zeus-operational-alpha/lib/pmct.py` | Discover an OA-01 verification through the configured legacy gate service | Same canonical Progressive OA runtime records | **BLOCKED WITH PRODUCTION CONTRACT**: its default is a production-qualification path through `GateApprovalService`; it cannot be safely redirected until that service has an explicit canonical adapter or is retired in favor of the Progressive OA lifecycle. |
| `scripts/tests/test-zeus-next-action.py` | Exercise next-action eligibility without mutating authoritative state | Isolated generated WOP/approval fixture | **REDIRECTABLE, NOT PARTIALLY CHANGED**: the test dependency can be replaced with a fixture, but the review stopped before partial modification because its production dependency still resolves through the incompatible legacy lifecycle. |
| `scripts/tests/test-zeus-gate-approval.py` | Supply isolated approval and eligibility primitives | Existing temporary WOP fixture with a fixture-owned approval primitive | **REDIRECTABLE, NOT PARTIALLY CHANGED**: the one copied external executable can be generated inside the existing temporary fixture, but the review stopped at the production blocker. |

The external records remain historical evidence only. In particular, the
unique approvals, decisions, and OA-01/OA-02/OA-19/OA-20/OA-21 verification
records were not imported, rewritten, or treated as current Progressive OA
authority.

Exact blocker: no repository implementation currently provides a
schema-compatible canonical replacement for the production
`GateApprovalService` persistence and lifecycle-command contract, and
`oa02_lifecycle.verify()` has no canonical record type with equivalent
identity, digest, and transition semantics. This establishes incompatibility,
not architectural necessity. The architectural reachability classification
below determines whether each consumer should be removed, narrowed, or
migrated. No compatibility adapter is proposed during Gate A.

Because redirection did not occur, the focused tests and required post-change
zero-reference/zero-user scans are not represented as successful exit
evidence. Freeze approval is not requested. The external root was observed
unchanged at mode `0755`, device `2065`, inode `2362046`; its manifest digest
remained `fbf1e69b4acc7a223aab1f547adc8698ae025912eaf82fd7e85c5121e2cd1f69`.

## Architectural reachability classification

Scope: the three repository files previously classified as production
consumers. The review searched definitions, imports, symbol calls, executable
entry points, Mission Contracts, the admitted Progressive OA package, EMP
orchestration, and EWI. Historical evidence references were treated as
provenance, not reachability.

The current runtime selects Progressive OA by default because
`engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json`
exists. In `scripts/zeus`, `progressive_enabled` is therefore true unless a
caller explicitly sets `ZEUS_PROGRESSIVE_OA=0`. Current `next-action`,
`status`, `verify OA-XX`, `approve OA-XX`, `decline OA-XX`, and `resume`
dispatch through `scripts.lib.emp.progressive_oa` and the gate-specific
Progressive verification modules. The admitted package's `BOOTSTRAP.md`
specifies that same execution path and states that it supersedes
`GH-ZEUS-OA-CERTIFICATION-001` for future OA execution.

### `scripts/lib/emp/oa02_lifecycle.py` — `DEAD CODE`

Every non-test call site:

| Call site | Reachability |
|---|---|
| `scripts/zeus` module import | Imported unconditionally, but import alone performs no lifecycle operation. |
| `scripts/zeus:authority_status()` | Calls `resolve_oa02`; `status` reaches this helper only on the non-Progressive orchestration branch. Current Progressive `status` returns `progressive_oa.status()` first. |
| `scripts/zeus` legacy `verify OA-02` branch | Calls `verify_oa02` only when `progressive_enabled` is false. Current Progressive execution calls `verify_oa02_gate` instead. |
| `scripts/lib/emp/next_action.py` | Imports `resolve_oa02` and calls it only after legacy OA-01 PMCT verification and acceptance. Current `zeus next-action` returns `progressive_oa.next_action()` before invoking this resolver. |

Test exercise is confined to `scripts/tests/test-zeus-next-action.py` and the
legacy-mode next-action assertions it contains. No Mission Contract names the
module, function, record type, or external path. The Progressive OA package
does not import or call it; its OA-02 authority, verification, marker,
acceptance, and lifecycle records are owned by the canonical Progressive
modules and runtime directories. EMP's core orchestration,
mission-admission, and mission-execution modules do not call it. EWI
(`scripts/lib/eos/platform.sh`, authorization-bundle resolution, and the
work-initiation shadow path) does not call or reference it.

Recommendation: remove `oa02_lifecycle.py`, its unconditional Zeus import,
its legacy branches, and its legacy-only tests rather than migrate its
external record. Preserve the external OA-02 verification as historical
evidence only.

### `scripts/lib/emp/gate_approval.py` — `ACTIVE TRANSITIONAL`

Every direct production importer and call family:

| Consumer | Calls |
|---|---|
| `scripts/zeus` | `_candidate_directories` in legacy status projection; `configured`, `binding`, carry-forward, legacy verify, legacy accept/decision, legacy approve, and agent-command dependencies |
| `scripts/lib/emp/next_action.py` | `configured`, `binding`, and `gate_milestone` for the superseded PMCT-bound OA-01 lifecycle |
| `scripts/lib/emp/oa02_lifecycle.py` | `configured`, candidate discovery, OA-01 binding, and milestone resolution |
| `scripts/lib/emp/agent_qualification.py` | `configured`, OA-01 binding/milestone, and OA-02 PMCT candidate validation |
| `scripts/lib/emp/gate_decision.py` | Receives `GateApprovalService` for legacy review and accept/reject decisions |
| `engineering/tests/zeus-operational-alpha/lib/pmct.py` | OA-01 verification discovery, prerequisite acceptance, and OA-02 lifecycle assertions |

The service remains directly reachable through installed Zeus command
surfaces including agent qualification and the legacy `accept` and
carry-forward operations; it is therefore not dead and not test-only.
However, it is not the authoritative Progressive OA gate lifecycle:
Progressive `verify`, `approve`, `decline`, `receipt`, and `resume` use
gate-specific verification plus `progressive_oa` JSON evidence, decisions,
and state. The canonical package's `BOOTSTRAP.md`, `runtime/state.json`, and
gate verification guides establish those owners. `gate_carry_forward.py`
lists `gate_approval.py` as protected historical OA-01 acceptance basis, which
preserves change sensitivity but does not make the legacy external WOP
current authority.

No Mission Contract directly identifies `gate_approval.py`,
`GateApprovalService`, its external record types, or its external path.
Progressive OA references the general PMCT contract and preserves prior OA
artifacts as historical evidence, but does not select this service as its
authority owner. EMP orchestration itself does not call the service; the
references are auxiliary EMP lifecycle modules and the Zeus operator
interface. EWI does not reference or call it.

Recommendation: do not design a compatibility adapter. Retire the legacy gate
approval, decision, next-action, carry-forward, and pre-Progressive agent
qualification dependencies from production command routing. Where an active
non-gate capability such as agent qualification is still required by a later
Progressive gate, make that capability consume its owning Progressive
predecessor receipts directly under a separately reviewed change. Remove the
external-dependent service after all transitional call sites are eliminated.

### `engineering/tests/zeus-operational-alpha/lib/pmct.py` — `ACTIVE TRANSITIONAL`

Every entry and caller:

| Call site | Reachability |
|---|---|
| `engineering/tests/zeus-operational-alpha/bin/pmct` | Direct executable wrapper that always invokes `lib/pmct.py`. |
| `scripts/install-engineering-cli` | Installs the PMCT wrapper as an engineering CLI. |
| `engineering/tests/zeus-operational-alpha/tests/test-*.py` | Import the module directly for contract, discovery, evidence, idempotency, result-model, cumulative-selection, and state-protection tests. |
| `scripts/lib/emp/gate_carry_forward.py` | Names the file as an OA-01 protected qualification path; this is change-impact detection, not execution. |

Within the harness, the external default is reachable in
`oa01_verification_state()`, `classify()` for the OA-01 prerequisite, and the
OA-02 assertion builder through `GateApprovalService.configured()`. A direct
`pmct run` can therefore exercise it. The harness is not test-only: it has an
installed executable, persists PMCT run evidence and capability state, and
the repository execution interface identifies `PMCT-CONTRACT` as an owning
contract.

It is nevertheless transitional rather than current OA authority. The
Progressive WOP references `PMCT-CONTRACT.md` and the capability matrix as
source and regression material, but current gate execution uses
`zeus verify OA-XX` and canonical `runtime/evidence/OA-XX` records; the
OA-06 guide does not invoke `pmct run`. The PMCT contract's independent
verification and acceptance sections describe the superseded external
`GateApprovalService` lifecycle, while the admitted Progressive package uses
JSON VERIFIED markers and Progressive decision receipts. No Mission Contract
directly names `lib/pmct.py` or its external lifecycle default. EMP
orchestration and EWI do not invoke the harness.

Recommendation: retain only the capability-observation and regression
functions that current Progressive verification actually requires, and
remove the legacy OA-01/OA-02 approval-lifecycle projections and their
external default. If no current Progressive verifier or controlled workflow
invokes the standalone harness after that narrowing review, remove the
installed wrapper and reclassify the remainder as test-only rather than
migrating it.

## Classification result

| Consumer | Classification | Adapter justified? | Gate A recommendation |
|---|---|---:|---|
| `scripts/lib/emp/oa02_lifecycle.py` | `DEAD CODE` | No | Remove legacy module, routing, and tests. |
| `scripts/lib/emp/gate_approval.py` | `ACTIVE TRANSITIONAL` | No | Eliminate transitional callers; route still-required capabilities to their existing Progressive owners without emulating the legacy WOP. |
| `engineering/tests/zeus-operational-alpha/lib/pmct.py` | `ACTIVE TRANSITIONAL` | No | Narrow to current capability/regression duties, remove legacy approval lifecycle, then reassess whether the executable remains production-required. |

No remaining consumer is `ACTIVE AUTHORITATIVE`. The architectural evidence
therefore does not justify a compatibility adapter. Gate A remains
`IN_PROGRESS — CONSUMER_REDIRECTION_REQUIRED`; the next safe change is a
bounded removal/narrowing plan for dead and transitional paths, followed by
isolated test-fixture conversion and the required zero-consumer and
active-user rescans. Gate B has not begun.
