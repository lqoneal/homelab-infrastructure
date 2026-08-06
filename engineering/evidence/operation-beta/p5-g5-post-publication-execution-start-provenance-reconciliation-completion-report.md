# P5-G5 Post-Publication Execution-Start Provenance Reconciliation

## Result

`P5_G5_POST_PUBLICATION_EXECUTION_START_PROVENANCE_RECONCILIATION_COMPLETE`

The execution-start verifier now consumes the canonical execution-start
provenance resolver. Immutable provenance is evaluated separately from the
current published baseline. Authority is resolved from the published
Operational Alpha authority chain; this session is not treated as an authority
source.

## Evidence

- Published repository baseline: `a16b3e3d72d23b265fdde5b6be4c40b90a48321e`
- Execution-start provenance baseline: `2507b441fdf0d083e35647e6874860365025ae18`
- Invocation provenance baseline: `b37a5fb2e11df8026afeff1bd231902cd54711ac`
- Current published baseline: `a16b3e3d72d23b265fdde5b6be4c40b90a48321e`
- Baseline relationship: `ANCESTOR`
- Execution-start integrity: `PASS`
- Execution ID preserved: `EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e`
- Execution session preserved: `EXECUTION-SESSION-0d35cea3-1232-58f7-b202-92d0bfc256a3`
- Execution-start mode: `QUALIFICATION_ADAPTER`
- Execution started: `YES`
- Mission work started: `NO`
- Repository work started: `NO`
- Execution monitoring active: `NO`
- Replay: `IDEMPOTENT`
- Provider contacted again: `NO`

The previous projection incorrectly exposed invocation provenance as
execution-start provenance. The corrective resolves execution-start provenance
from the immutable execution-start transaction/package/session/receipt chain,
preserves invocation provenance independently, and exposes current publication
metadata separately. It accepts `IDENTICAL` and `ANCESTOR` relationships
without changing immutable execution identity.

## Verification

The canonical resolver accepts `IDENTICAL` and `ANCESTOR`, and rejects
unrelated or missing provenance, repository/runtime mismatches, and changed
execution-critical bindings. Focused execution-start, runtime-discovery, and
canonical-baseline tests passed: `16 passed`.

Read-only Zeus verification reports execution-start `PASS`, execution-start
provenance `2507…`, invocation provenance `b37…`, current publication `a16…`,
execution-start relationship `ANCESTOR`, integrity `PASS`, mission work `NO`,
blockers `NONE`, and next action `BEGIN_CONTROLLED_MISSION_WORK`. No
execution-start, invocation, session, dispatch, provider, Codex, mission-work,
repository-work, publication, or EOS state was created or modified by this
corrective.

## Changed-file inventory

- `scripts/lib/eos/canonical_baseline.py`
- `scripts/lib/emp/execution_start.py`
- `scripts/lib/emp/canonical_runtime_mission.py`
- `scripts/lib/emp/mission_verification_controller.py`
- `scripts/lib/emp/publication_workflow.py`
- `scripts/tests/test-zeus-p4-g3-runtime-discovery.py`
- `scripts/tests/test-zeus-p5-g4-provider-invocation.py`
- `scripts/tests/test-zeus-p5-g5-execution-start.py`
- `scripts/zeus`
- `engineering/evidence/operation-beta/p5-g5-post-publication-execution-start-provenance-reconciliation-completion-report.md`

The evidence path is authorized explicitly by the same canonical publication
scope source. No wildcard or operator-specific scope exception was added.

## P5-G6 preparation

No Zeus–Codex adapter, launch path, CLI, process/session integration, or
provider behavior was added. That work remains deferred to P5-G6.

## Deferred boundary

Publication and EOS synchronization were not performed. The next action is
operator review. No P5-G6 work was started.
