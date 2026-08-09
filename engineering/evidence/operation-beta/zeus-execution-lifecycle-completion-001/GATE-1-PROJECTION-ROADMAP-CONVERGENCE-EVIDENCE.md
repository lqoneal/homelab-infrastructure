# WOP Gate 1 Projection and Roadmap Convergence Evidence

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`  
WOP: `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001`  
Corrective gate: WOP Gate 1, `LIFECYCLE-AUTHORITY-CONVERGENCE`  
Stop boundary: `OPERATOR_REVIEW`

This record qualifies only the bounded Gate 1 projection corrective and the
secondary instruction-handoff contract. It does not authorize or record
`BEGIN_CONTROLLED_MISSION_WORK`, repository-work activation, session
supersession, monitoring activation, completion, publication, EOS
synchronization, or closeout.

## Starting repository and runtime condition

| Coordinate | Starting value |
| --- | --- |
| repository | `/data/engineering/repositories/homelab` |
| canonical remote | `git@github.com:lqoneal/homelab-infrastructure.git` |
| repository ID | `homelab-6bd83f9079d6fc57` |
| repository fingerprint | `6bd83f9079d6fc57` |
| branch | `main` |
| HEAD | `e7e48ab6b523d94e73d40fb4311f86bc7118b0b1` |
| origin/main | `e7e48ab6b523d94e73d40fb4311f86bc7118b0b1` |
| ahead / behind | `0 / 0` |
| EOS baseline | `e7e48ab6b523d94e73d40fb4311f86bc7118b0b1` |
| HEAD / origin / EOS parity | `PASS / PASS / PASS` |
| index | clean |
| worktree | dirty before this corrective; all unrelated modified and untracked paths preserved |

The starting read-only lifecycle projection was already receipt-backed and
resolved to `READY_FOR_CONTROLLED_EXECUTION`, with both work-started flags
false and `BEGIN_CONTROLLED_MISSION_WORK` as the lifecycle next action. The
Codex runtime was independently classified `STALE_ORPHANED_RUNTIME`, with
`SUPERSEDE_CODEX_SESSION` as its subordinate recovery action.

## Before correction

| Surface | Before |
| --- | --- |
| `zeus mission verify/show/state/next/snapshot` | live lifecycle mission, exact WOP, `READY_FOR_CONTROLLED_EXECUTION`, work flags false, `BEGIN_CONTROLLED_MISSION_WORK` |
| `zeus execution-start verify` | live lifecycle mission and execution-start identities, same state and boundary |
| `zeus codex status` | live lifecycle mission, stale orphan classification, recovery separate from lifecycle action |
| `zeus operation ... OPERATION-BETA` | `UNKNOWN_OPERATION` because only the noncanonical `BETA` alias was accepted |
| legacy Beta operation projection | no receipt-backed lifecycle mission ingestion; planning card selection exposed `CAGF-01` as the executable next position |
| controlled roadmap text | retained stale snapshots saying no current executable mission and/or treating `CAGF-01` as current |
| WOP/global gate relationship | no explicit deterministic Gate 1/Gate 4 crosswalk |

## Root cause

One ownership defect produced the apparent contradictions:

1. `scripts/lib/eos/operational_beta.py` derived current executable work only
   from legacy roadmap-card admission/execution projection. It did not ingest
   `canonical_lifecycle_resolver.submitted_missions()` and `resolve()`.
2. The same operation resolver used roadmap ordering and candidate selection
   to compute its global next action. A planning recommendation therefore
   masqueraded as execution authority.
3. Separate status fields consumed the lifecycle resolver, producing two
   incompatible current-position owners within Operation Beta.
4. The CLI did not accept canonical `OPERATION-BETA`, and the controlled gate
   catalog did not carry the required WOP/global crosswalk.
5. Current-position prose preserved earlier planning snapshots after live
   lifecycle receipts had overtaken them.

Classification: missing active-mission ingestion, candidate-versus-authority
precedence defect, roadmap ordering treated as executable selection, missing
WOP/gate crosswalk, stale embedded/current-position baselines, and canonical
operation alias mismatch. There was no evidence that the lifecycle mission
itself, its receipts, or its identity chain was defective.

## Singular ownership model

| Coordinate | Authoritative owner | Derived consumer rule |
| --- | --- | --- |
| current Operation Beta execution position | Operation projection over canonical lifecycle receipts | exactly one nonterminal submitted mission; ambiguity fails closed |
| current executable mission | canonical lifecycle resolver | roadmap cards cannot supply or replace it |
| current lifecycle mission identity | immutable Mission/WOP receipt chain | preserve every bound identity |
| current WOP | canonical lifecycle resolver | preserve receipt-backed `wop_id` |
| current lifecycle state | canonical lifecycle resolver | planning documents cannot invent runtime state |
| current lifecycle next action | canonical lifecycle resolver | stage-local and recovery actions remain subordinate |
| current WOP/global gate mapping | controlled Operation Beta gate catalog | state-to-crosswalk resolution must be singular |
| global roadmap recommendation | Operation Beta roadmap/card selector | planning only; no execution authority |
| future mission recommendation | Operation Beta roadmap/card selector | remains separately discoverable as `CAGF-01` |
| runtime recovery action | Codex history/liveness reconciliation | cannot replace the lifecycle next action |

The enforced semantic rule is `CURRENT_EXECUTION != FUTURE_RECOMMENDATION`.

## Implementation and crosswalk

The Operation Beta resolver now consumes the canonical receipt-backed
lifecycle index and resolver, rejects multiple or contradictory active
records, excludes terminal/historical records, preserves identity and work
flags, and projects runtime recovery separately. Its public operation and
authority views use the live projection. Upstream receipt verifiers use an
explicit planning-authority-only mode so authority verification does not
recursively call the downstream lifecycle resolver.

The controlled crosswalk is:

| WOP position | Operation Beta position | Relationship |
| --- | --- | --- |
| Gate 1 `LIFECYCLE-AUTHORITY-CONVERGENCE` | `OB-ARCH-G01` | local convergence corrective; no runtime authority effect; stop at `OPERATOR_REVIEW` |
| Gate 4 `CONTROLLED-EXECUTION-AND-RECOVERY` | `OB-ZEUS-G01` | current lifecycle capability position for `READY_FOR_CONTROLLED_EXECUTION` and controlled-work states; no authority grant |

The Gate 4 mapping is a current-position projection only. Gate 4 work remains
held by this handoff's stop boundary.

## After correction

All supported Operation Beta `show`, `status`, `roadmap`, and `next-action`
views now accept `OPERATION-BETA` and resolve:

| Coordinate | Value |
| --- | --- |
| current operation | `OPERATION-BETA` |
| current executable mission | `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` |
| current WOP | `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001` |
| lifecycle state | `READY_FOR_CONTROLLED_EXECUTION` |
| gate mapping | WOP Gate 4 `CONTROLLED-EXECUTION-AND-RECOVERY` / `OB-ZEUS-G01` |
| mission work started | `false` |
| repository work started | `false` |
| lifecycle next action | `BEGIN_CONTROLLED_MISSION_WORK` |
| future recommendation | `CAGF-01` |
| runtime classification | `STALE_ORPHANED_RUNTIME` |
| runtime recovery action | `SUPERSEDE_CODEX_SESSION` |

The public Operation Beta authority projection independently reports
`active_gate=OB-ZEUS-G01` and
`next_authorized_action=BEGIN_CONTROLLED_MISSION_WORK`.

## Identity preservation

| Identity | Preserved value |
| --- | --- |
| submission | `SUBMISSION-a2c024ce-077a-5d70-bb1d-067e056e5a23` |
| admission | `ADMISSION-264c5bc0-4812-54d5-8f03-353d0cd0a899` |
| bootstrap | `BOOTSTRAP-4e6bd7f6-4489-5378-92c4-e3ea42782ec4` |
| dispatch | `DISPATCH-18865edc-5878-57c0-ae43-c697f01e3325` |
| provider | `zeus-local-loneal-01` |
| provider session | `PROVIDER-SESSION-309031db-d38a-5bf9-8db3-b871ed2ddfd1` |
| provider invocation | `PROVIDER-INVOCATION-ccbf4655-b0f4-57b2-8a1a-3fea9a3d88f9` |
| execution start | `EXECUTION-START-03e0a183-23a4-5dc7-b6dc-bc62c1a9a1ae` |
| execution session | `EXECUTION-SESSION-13637768-524b-5587-8d01-1cce5f301b80` |
| Codex session | `CODEX-SESSION-8e97324a-cdd7-5189-acaf-a37682cb24ee` |

No receipt or historical evidence was rewritten.

## Cross-surface matrix

| Surface | Before | After | Authority |
| --- | --- | --- | --- |
| Operation Beta show/status/roadmap | unavailable under canonical operation ID; planning candidate was executable position | live mission/WOP/state/gate/action plus separate future CAGF | canonical lifecycle resolver + controlled crosswalk |
| Operation Beta next-action | planning candidate action | `BEGIN_CONTROLLED_MISSION_WORK`; CAGF separate | canonical lifecycle resolver |
| public Beta authority | planning gate | `OB-ZEUS-G01` and lifecycle action | live operation projection |
| mission verify/show/state/next/snapshot | correct live lifecycle mission | unchanged and converged | canonical lifecycle resolver |
| execution-start verify | correct live execution start | unchanged and converged | immutable execution-start receipts |
| Codex status | stale recovery beside lifecycle action | unchanged and explicitly subordinate | Codex liveness/history reconciliation |
| controlled roadmap | stale no-current/CAGF-current snapshots | current execution and future recommendation separated | controlled planning record over live projection |

## Replay and tests

Two consecutive `zeus operation show OPERATION-BETA --json` projections
produced the identical SHA-256 digest
`e01273f470f2a345cfecd13811a4e8c3ef74147d53587982ced81107ab9e9042`.
Two consecutive structured-handoff projections produced the identical digest
`9f41e8b9d5138c9733db840e91731fd1be91b4715db5249dca8ffde6323c8d8f`.

Passing verification:

- operation lifecycle convergence: 12 tests
- Beta controller: 5 tests
- Beta mission selection convergence: 3 tests
- managed Codex handoff: 20 tests
- canonical lifecycle resolver: 10 tests
- mission verification controller: 5 tests
- Codex adapter: 32 tests passed, 2 skipped
- Beta mission projection and platform invariants: pass
- controlled-document structural validation: 2,897 passed, 0 failed
- controlled-document semantic-all validation: 3,805 passed, 0 failed
- affected Python modules: byte-compilation pass
- handoff schema self-validation and example validation: pass
- Zeus platform verification: pass
- `git diff --check`: pass

The mission-verification relocation fixture now excludes the non-authoritative
6.3 GB `codex-home` installation/cache from its temporary runtime copy. The
fixture remains bounded to the receipt/runtime artifacts that mission
verification consumes; all five tests pass without deleting or mutating the
live runtime.

## Controlled-document reconciliation

Current-position statements in the Operation Beta authority model, roadmap,
canonical gate catalog, canonical development roadmap, lifecycle remediation
plan, Beta controller integration, and mission projection specification now
separate live execution from future planning. Earlier planning observations
are retained and classified as superseded snapshots. The authored WOP source
is preserved; this evidence provides Gate 1 traceability without rewriting its
immutable requirements or claiming later gates complete.

## Canonical structured handoff contract

Discovery found an existing controlled handoff owner:
`PROC-0004-ENGINEERING_HANDOFF_CONSTRUCTION_PROCEDURE.md`. It defined the
repository-driven handoff and safe file/STDIN transport, but did not define a
schema-valid task-fact payload. The existing
`engineering/oversight/work-contract.schema.yaml` governs managed continuation
after an execution already exists and is intentionally not reused as a second
instruction or execution authority.

PROC-0004 is therefore retained as the stable instruction owner and is
extended by the minimum task payload schema:

- schema: `engineering/oversight/codex-handoff-contract.schema.yaml`
- example: `engineering/oversight/examples/zeus-execution-lifecycle-gate1-handoff.yaml`
- resolver: existing `scripts/zeus codex handoff` / managed-handoff path

The standard is:

```text
STABLE INSTRUCTIONS -> reference controlled contract
TASK-SPECIFIC FACTS -> schema-valid YAML/JSON payload
NOVEL REASONING -> concise natural_language_context only when required
```

CLI-safe use is immediate and does not invent a prompt-file option:

```bash
scripts/zeus codex handoff engineering/oversight/examples/zeus-execution-lifecycle-gate1-handoff.yaml --json
scripts/zeus codex handoff - --json < engineering/oversight/examples/zeus-execution-lifecycle-gate1-handoff.yaml
```

Legacy prose handoffs remain compatible. Historical handoff evidence is not
rewritten. The resolver reports `execution_authority=NONE` and
`mutation_applied=false`; the payload carries bounded instructions only. It
does not alter Mission/WOP authority, approval, execution/provider/session
identity, Zeus process ownership, STDIO transport, recovery, or supersession.

## Remaining Gate 4 work

Gate 4 still requires a separately qualified machine work-unit/action
contract, repository-work activation evidence, execution monitoring/current
position semantics, blocker/approval contract, and controlled stale-session
recovery. None was activated here.

Gate 1 result: `PASS`, pending operator review.  
Ready for Gate 4 specification/qualification: `YES`.  
Ready for real controlled execution: `NO`.  
Next single action: independently specify and qualify Gate 4 contracts while
preserving `OPERATOR_REVIEW`; do not begin controlled mission work.
