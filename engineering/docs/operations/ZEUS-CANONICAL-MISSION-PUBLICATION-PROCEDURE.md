# Zeus Canonical Mission Publication Procedure

After a Development publication WOP is qualified, Zeus resolves its immutable
target linkage. Publication approval, synchronized EOS, and passing platform
validation are mandatory before activation. Activation creates exactly one
active Mission Contract, one Beta registry work item, and one digest-bound
operational package binding.

Before publication, `zeus mission show STOPQ-01 --json` reports blocked
canonical discovery with the Development transaction and next action. After
publication, the same command family must report exactly one active contract,
registry entry, package, authority, blocker set, and next action.

## Zeus-native publication transaction controller

Current publication is a durable Zeus transaction, not an untracked sequence of
Git commands. The canonical command family is:

```text
zeus publication inspect <MISSION_ID> --json
zeus publication classify <MISSION_ID> --json
zeus publication prepare <MISSION_ID> --json
zeus publication verify-pre <PUBLICATION_ID> --json
zeus publication stage <PUBLICATION_ID> --json
zeus publication commit <PUBLICATION_ID> --json
zeus publication push <PUBLICATION_ID> --json
zeus publication synchronize <PUBLICATION_ID> --json
zeus publication qualify <PUBLICATION_ID> --json
zeus publication status <PUBLICATION_ID> --json
zeus publication resume <PUBLICATION_ID> --json
zeus publication abort <PUBLICATION_ID> --json
zeus publication run <MISSION_ID> --json
```

`run` performs inspection, classification, preparation, and prepublication
verification in review mode unless `--approve` is supplied. Approval crosses
the existing publication approval boundary; it does not create a second
authority grant. Every mutating transition requires a writable
repository-bound runtime and records an immutable milestone receipt.

`PREPUBLICATION_VERIFIED` is a durable transaction milestone, not a transient
validator result. A passing prepublication verification writes the immutable
receipt, binds its digest in the transaction, persists
`prepublication_result=PASS` and `current_state=PREPUBLICATION_VERIFIED`, then
reloads and validates that transaction before the controller may return
`STAGE_PUBLICATION_CANDIDATE`. `publication verify` remains a compatibility
spelling for `publication verify-pre`.

The transaction state resolver is the sole owner of the publication next
action. Candidate/cohort revalidation, status, mission projection, and CLI
rendering may report blockers but may not promote a transient PASS or an
unreferenced receipt into staging authority. Verification or transaction
persistence failure is fail-closed. A receipt left without a valid persisted
transaction reference grants no authority. Replaying successful `verify-pre`
revalidates the frozen inputs, reuses the same receipt lineage, leaves the Git
index unchanged, and cannot advance beyond staging readiness.

Candidate membership comes from a qualified publication manifest or equivalent
authoritative traceability source. Dirty status alone is never publication
authority. The frozen candidate set is consumed by later stages; unexpected
staged paths, partial overlap, changed candidate content, ambiguous
classification, and missing paths fail closed. Unrelated dirty, historical,
generated, and legacy paths remain preserved and unstaged.

The transaction binds repository identity, Mission/WOP identity, starting
HEAD/origin/EOS projection, candidate and classification digests, commit,
remote ref, published baseline, synchronization result, postpublication
verification, completed milestones, blockers, and next action. Replay resumes
from the latest qualified milestone: a successful commit is not recreated
before push, a successful push is not repeated before EOS synchronization, and
an EOS failure does not rewrite published Git history. Postpublication
verification resolves the mission from live repository/EOS projections and
verified descendant lineage; it does not treat an immutable receipt baseline
as a permanent current-state literal.

Controller-owned network operations use `GIT_TERMINAL_PROMPT=0` and explicit
refs. Operator-interactive credential behavior remains available to manual
workflows outside the controller. JSON output and exit codes are the machine
contract: zero means the requested transition or review result resolved;
nonzero means failure, blocker, or unresolved state.

### Machine interface rule

Publication automation uses canonical publication and cohort identifiers,
typed Zeus operations, explicit authority/state operands, deterministic exit
codes, and structured JSON/YAML contracts/results. Equivalent executable work
is represented structurally rather than by authoritative natural-language
prose. Current publication operands are resolved from live Zeus projections;
hardcoded runtime or current-state data is a documented last resort. This
rule applies to publication, qualification, synchronization, and the related
mission/WOP lifecycle interfaces without creating a parallel controller.
## Mission-scoped publication-candidate authority

Native publication candidate resolution begins with the live canonical mission
and WOP projection.  It then follows qualified completion/evidence records to
their publication-candidate manifests and resolves the deterministic union of
authorized source paths.  Dirty status, filename similarity, directory
membership, and manifest existence alone are not publication authority.

Each selected source records its manifest, mission/WOP binding, qualification
state, publication state, dependency relationship, and selection reason.  A
path without non-null authority is not eligible.  Historical, already-published,
unrelated, superseded, ambiguous, blocked, and invalid sources remain visible
as exclusions; they are never silently folded into the current candidate.
Multiple qualified manifests may contribute to one transaction.  Conflicting
current claims, missing dependencies, missing manifest paths, or an unresolved
mission/WOP relationship fail closed.  Exact replay produces the same source
and path digests and cannot create a second publication transaction.

The controller consumes this resolver; it does not replace it with an
operator-authored path list or a second Git projection.  `publication
classify` exposes `candidate_sources`, `candidate_paths`, `candidate_digest`,
`classification_digest`, `already_published`, `blocked`, `ambiguous`, and
`missing` in JSON.  `publication prepare` freezes those resolved inputs and
binds them to the durable publication transaction.  A changed source,
qualification record, repository projection, or candidate digest requires
reclassification/reconciliation before a later transition.

The resolver may use an explicitly supplied, qualified machine-readable
manifest as a bounded engineering/test fallback when no live mission
projection is available.  That fallback must bind both mission and WOP, is
never the normal runtime authority, and fails closed on identity conflict.

## Source-level publication cohort authority

Mission/WOP membership and `QUALIFIED_UNPUBLISHED` status identify eligible
work sources, but they do not by themselves authorize those sources to
converge in one publication transaction. Zeus therefore may persist one
repository-bound Publication Cohort that names qualified source identities and
required source-level dependencies. Candidate paths remain derived from the
member sources' authoritative manifests; a cohort is never a manually curated
Git path list.

The cohort is bound to the live Mission ID, WOP ID, repository identity,
qualified source digests, and current repository provenance. An overlapping
path claimed by multiple qualified sources is valid only when every current
claim belongs to the same active cohort. Claims outside the cohort, missing or
unqualified dependencies, changed source qualification, wrong identity, and
source supersession ambiguity fail closed. Historical, later, and follow-on
records remain visible as excluded source evidence.

When a cohort supersedes an immutable candidate transaction, the replacement
transaction records `publication_cohort_id` and `supersedes_publication_id`.
The predecessor's frozen candidate, digests, and milestone receipts are not
rewritten. Mission lookup excludes a superseded predecessor through the
successor linkage while preserving the predecessor for historical audit.

The native inspection surface exposes cohort authority, source membership,
dependencies, exclusions, shared-path resolution, and blockers. Cohort
establishment is replay-safe and fails closed when the live source projection
changes. A cohort does not authorize staging; the next publication transition
remains independently gated by `STAGE_PUBLICATION_CANDIDATE`.

Transaction-scoped `inspect`, `status`, `verify`, `stage`, and `resume`
revalidation begin with the persisted transaction's
`publication_cohort_id`. They load that exact durable cohort, resolve the live
member manifests and qualification state, reconstruct the member candidate
paths and content digest, and compare the live candidate and authority
identity with the frozen transaction inputs. They do not broaden authority to
the mission's current `QUALIFIED_UNPUBLISHED` discovery set. A later
qualified source outside the cohort is therefore not transaction drift; a
changed or missing cohort member, qualification, manifest/path, or candidate
content remains `STALE_CLASSIFICATION` and fails closed. Missing or mismatched
cohort identity also fails closed.
