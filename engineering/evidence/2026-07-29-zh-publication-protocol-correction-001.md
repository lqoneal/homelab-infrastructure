# ZH Publication Protocol Correction 001

Date: 2026-07-29  
Handoff: `ZH-PUBLICATION-PROTOCOL-CORRECTION-001`  
Disposition: `PROTOCOL CORRECTED — PUBLICATION REMAINS PAUSED`

## 1. Engineering Work Initiation

| Check | Observed result |
| --- | --- |
| Repository identity | `/data/engineering/repositories/homelab`; `git@github.com:lqoneal/homelab-infrastructure.git`; canonical Git root verified |
| Branch and HEAD | `main`; `a85893930e83c2a0579e465f4951499965441f11` |
| Upstream | `origin/main` at `f79462b`; local branch ahead 1, behind 0 |
| Publication status | PU-01 successfully completed as `a858939`; PU-02 through PU-09 not executed and publication paused |
| Working tree | Pre-existing multi-unit publication candidate present; initially 72 modified/untracked paths reported by repository health |
| Repository health | PASS: discovery, integrity, and active branch; expected modified candidate reported |
| Work Registry | PASS: revision 85, 85 objects, authority boundary valid |
| EOS comparison | Read-only `engctl eos sync-validate homelab` reported drift in `EOS-STATE.md` and `EOS-MANIFEST.md` |
| Checkpoint comparison | Read-only status reported checkpoint `bcdd0b1a1904` and repository `a85893930e83` as drifted |
| Mutation controls | No resume, synchronize, refresh, checkpoint, stage, commit, push, lifecycle, gate, or declaration command invoked |

The dirty-tree exception is the handoff's bounded documentation correction
against the already inventoried publication candidate. Existing changes were
preserved. This work modifies only the protocol documents and evidence listed
in the change matrix.

## 2. Repository evidence summary

Repository evidence establishes a one-way authority model:

- `engineering/eos/repository-eos-authority.yaml` assigns repository ownership
  for synchronized engineering state.
- `engineering/operations/repository-eos-synchronization.md` documents
  deterministic repository-to-EOS rendering and a read-only exact comparison.
- EOS-0003 identifies `EOS-ID.md`, `EOS-STATE.md`, and `EOS-MANIFEST.md` as
  regenerable derived projections that are not published and never hold
  independent engineering-state authority.
- Current HEAD is the completed PU-01 publication commit, while EOS remains at
  the earlier synchronized baseline. The observed mismatch is therefore caused
  by repository publication preceding the plan's later state-projection
  boundary.
- `engctl resume` can mutate derived/cache state. It is consequently unsuitable
  as a read-only validator inside a publication sequence.

Conclusion: PU-01 did not fail merely because EOS did not change with it.
Repository commits do not automatically synchronize EOS. The current mismatch
is `EXPECTED_PUBLICATION_DRIFT`, and synchronization remains prohibited until
the declared boundary and separate authority exist.

## 3. Updated synchronization contract

Repository content is authoritative. EOS is a derived runtime projection and
never becomes authoritative over working-tree, committed, or published
repository state. Projection flows repository-to-EOS only.

The corrected contract distinguishes:

1. **Working-tree projection** — what current source bytes would render.
2. **Committed projection** — what a selected local commit would render.
3. **Published projection** — what the completed published baseline would
   render.
4. **Synchronized EOS projection** — what an authorized synchronization
   actually persisted and exact post-validation confirmed.

Every future publication plan must declare:

1. **Initial Validation Boundary** — read-only baseline and prerequisite
   validation.
2. **Publication Boundary** — exact repository transaction(s).
3. **Synchronization Boundary** — separately authorized repository-to-EOS
   projection point.
4. **Final Validation Boundary** — final repository and applicable synchronized
   EOS/runtime verification.

Omission of a Synchronization Boundary means EOS synchronization is out of
scope. Commit, push, publication, write, or validation authority does not imply
synchronization authority.

## 4. Documentation changes

PROC-0005 now owns the boundary declaration, projection vocabulary, drift
classification, synchronization separation, and phase-specific publication
validation rules. PROC-0001 applies those rules during publication Work
Initiation. STD-0004 no longer treats declared intermediate publication drift
as stale authoritative state. EOS-0003 and the operational synchronization
guide state the same one-way contract. DOC-0001 records the coordinated
revision set.

The current publication plan now records PU-01 completion, the pause, and the
requirement for a new execution handoff that references the corrected
procedure. The detailed affected-document matrix is:
`engineering/evidence/2026-07-29-zh-publication-protocol-correction-001-change-matrix.md`.

## 5. Procedure changes

Before execution, the publication executor must record all four boundaries,
the operator and authority for each effect, selected full commit, target
project, prerequisites, validation commands, and stop conditions.

At intermediate Publication Boundaries, repository checks run normally and EOS
comparison remains read-only. Expected drift is recorded without repair. At
the Synchronization Boundary, publication advancement stops. Only the named
operator holding explicit synchronization authority may invoke
`engctl eos synchronize`, and only after repository health, registry, package,
diff/committed-path, and source validations pass. Exact synchronization,
EOS state/persistence, and integrated platform checks follow immediately.

## 6. Validation changes

| Phase | Required validation |
| --- | --- |
| Before publication | Repository identity/HEAD, health, registry, applicable package verification, working-tree/diff inventory, publication-plan integrity, read-only EOS comparison |
| During publication | Exact staged and committed path verification, `git diff --check`, unit-specific tests, repository health, affected registry/package validation, read-only EOS comparison and classification |
| At Synchronization Boundary | All prerequisites above against selected full commit; explicit authority; synchronization only if authorized; immediate exact sync, EOS state/persistence, and integrated platform verification |
| After final publication | Final repository health, registry, package, committed path/diff, full publication matrix, and either verified synchronized EOS projection or an explicit out-of-scope/expected-drift disposition |

Validation observes state; it does not create synchronization, publication, or
repair authority.

## 7. Drift classification model

| Classification | Operator action |
| --- | --- |
| `EXPECTED_PUBLICATION_DRIFT` | Record repository and EOS baselines; do not synchronize; continue only within the approved sequence. |
| `SYNCHRONIZATION_REQUIRED` | Pause advancement at the declared boundary and verify separate authority and prerequisites. |
| `SYNCHRONIZATION_FAILURE` | Stop, preserve evidence and repository authority, diagnose EOS, and retry only under applicable authority. |
| `AUTHORITATIVE_SOURCE_FAILURE` | Stop publication and correct repository sources under separate authority; never repair repository content from EOS. |
| `RUNTIME_STATE_FAILURE` | Stop runtime-dependent work and repair only the affected EOS runtime domain under operational authority. |

## 8. Cross-reference reconciliation

The coordinated cross-reference chain is:

`PROC-0001 -> PROC-0005 -> STD-0004 / EOS-0003 ->
engineering/operations/repository-eos-synchronization.md`.

PROC-0005 now declares direct relationships to STD-0004 and EOS-0003. DOC-0001
already indexes all four controlled records and now records their coordinated
revisions. The publication plan references corrected PROC-0005 instead of
embedding synchronization as an incidental validation step.

Historical evidence remains unchanged because it truthfully records earlier
events. General reconciliation requirements remain applicable, but they cannot
override the new publication-specific boundary and authority rules.

Final consistency validation:

| Check | Result |
| --- | --- |
| Controlled-document validation | PASS: 2,647 checks, 0 failures |
| Governance baseline documentation tests | PASS: 5 tests |
| Progressive OA package verification | PASS: 30 unique cumulative gates and complete contracts |
| Registry validation | PASS: revision 85 / 85 objects and authority boundary |
| Repository health | PASS: identity, integrity, branch; expected dirty candidate reported |
| Diff/whitespace integrity | PASS: `git diff --check` |
| Cross-reference integrity | PASS: controlled relationships resolve and all corrected-protocol paths exist |
| Terminology and contract consistency | PASS: four boundaries, four projection terms, and five drift classes resolve across the governing chain |
| EOS comparison | Expected nonzero result: `EOS-STATE.md` and `EOS-MANIFEST.md` classified `EXPECTED_PUBLICATION_DRIFT`; no synchronization invoked |
| Publication mutation check | PASS: HEAD remains `a85893930e83c2a0579e465f4951499965441f11`; index remains unstaged |

## 9. Risks

- Existing tooling still emits a binary `aligned`/`drifted` observation; the
  publication operator must apply the documented classification.
- `engctl resume` may auto-repair derived/cache drift and must not be used for
  read-only publication boundary validation.
- A later handoff that copies the old validation paragraph instead of
  referencing PROC-0005 could recreate the ambiguity.
- The current large dirty candidate requires exact path isolation when
  publication resumes.
- Controlled-document revisions remain pending their applicable review and
  publication authority; this handoff does not publish or activate them.

## 10. Final recommendation

Approve the corrected protocol for use by a new, separately authorized
publication execution handoff. That handoff should reference PROC-0005 Version
1.5 or later, declare all four boundaries, name the synchronization authority,
and retain the plan's Synchronization Boundary after PU-08.

Do not resume PU-02 or later publication under the previous protocol. Do not
synchronize EOS during this correction. Repository publication remains paused
after successful PU-01 pending approval of the revised protocol. No gate
advancement or Operational Alpha declaration is authorized or performed.
