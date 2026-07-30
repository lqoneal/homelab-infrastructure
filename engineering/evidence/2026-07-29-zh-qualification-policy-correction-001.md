# ZH Qualification Policy Correction 001

Date: 2026-07-29
Handoff: `ZH-QUALIFICATION-POLICY-CORRECTION-001`
Disposition: `PROCEDURE CORRECTION COMPLETE — PUBLICATION REMAINS PAUSED`

## 1. Engineering Work Initiation

| Check | Result |
| --- | --- |
| Repository identity and root | `/data/engineering/repositories/homelab` |
| Remote | `git@github.com:lqoneal/homelab-infrastructure.git` |
| Branch | `main` |
| HEAD | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Upstream | `origin/main`; ahead 2, behind 0 |
| Repository health | PASS: discovery, integrity, and active branch |
| Registry validity | PASS: 85 objects; schema, hierarchy, ordering, states, deferrals, dependencies, and authority boundary |
| PU-01 | `a85893930e83c2a0579e465f4951499965441f11` |
| PU-01A | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Publication state | Paused immediately after PU-01A |
| Index | Empty |
| Qualification procedures | PROC-0006 and PROC-0001 reviewed |
| Publication procedure | PROC-0005 reviewed |
| Validation procedures | PROC-0005 validation model, PROC-0006 finding classification, PROC-0001 validator evidence, SPEC-0001 Markdown integrity, and repository validators reviewed |

No staging, commit, amendment, reset, rebase, synchronization, push,
publication execution, publication planning, or publication-unit reassignment
occurred.

## 2. Repository Baseline

PU-01A is the current immutable local commit. The 14-path commit, reconciled
membership, and reconciled digests are unchanged. The remaining reconciled
publication candidate remains in the working tree. The prior execution report
is preserved as uncommitted evidence, and this correction adds only the three
procedure revisions and two required evidence files listed in the change
matrix.

The authoritative publication plan and reconciliation manifest were inspected
but not modified. EOS was not synchronized. Publication remains paused before
PU-02.

## 3. Validation-Policy Analysis

`git diff --check` protects the publication boundary by detecting introduced
whitespace errors and conflict markers. Its raw output and exit status are
objective evidence and must be retained.

The command does not determine:

- whether Markdown renders with the intended line break;
- whether controlled-document meaning is correct;
- whether metadata or cross-references are valid;
- whether a publication set matches its manifest;
- whether Git objects or repository history are valid; or
- whether a publication transaction passed its other required controls.

The protected failure classes are conflict markers, space-before-tab
indentation, whitespace-only lines, accidental trailing whitespace, and
unclassified or ambiguous findings. Those findings block qualification.

An individually confirmed Markdown hard break is a formatting finding.
Advisory or observational tool output remains recorded but is non-blocking only
when the governing procedure explicitly classifies it that way. Semantic,
structural, cross-reference, and repository-integrity failures remain blocking
regardless of whitespace disposition.

## 4. Markdown Qualification Analysis

SPEC-0001 establishes Markdown with YAML front matter as the current controlled
document representation and requires Markdown integrity. Markdown represents a
hard line break using two terminal ASCII spaces after non-whitespace content.
That byte sequence therefore has valid representation semantics and cannot be
classified as accidental whitespace solely because a file-independent detector
reports it.

The repository does not define a `.gitattributes`, `.editorconfig`, or
`core.whitespace` rule that changes `git diff --check` behavior for Markdown.
Earlier repository evidence preserved Markdown whitespace warnings as
candidate quality findings rather than silently editing them. The supported
conclusion is conditional permission, not a blanket Markdown exemption.

The authoritative qualification rule is:

1. run `git diff --check` across the exact boundary and preserve its output and
   exit status;
2. treat all protected or ambiguous findings as blocking;
3. permit exactly two ASCII terminal spaces after non-whitespace Markdown
   content only when the line is identified and confirmed as an intentional
   hard break;
4. reject three or more spaces, blank-line whitespace, tabs asserted as hard
   breaks, and accidental editor padding;
5. apply the exception to generated Markdown only when a controlled generator
   contract requires the break and deterministic regeneration reproduces it;
   and
6. never use this classification to excuse semantic, structural,
   cross-reference, manifest, digest, repository-integrity, or conflict-marker
   failures.

## 5. Procedure Consistency Review

PROC-0005 now owns the single publication whitespace policy. It keeps
`git diff --check` mandatory for all file types and defines the narrow
file-type-aware classification.

PROC-0006 now consumes PROC-0005 when publication qualification uses the
command. It distinguishes raw tool status from the governed qualification
result and leaves ambiguous findings blocking.

PROC-0001 now requires execution evidence to retain both raw validator status
and any separately governed classification. This preserves its existing rule
that later commands cannot mask a validator result.

PROC-0007, STD-0001 through STD-0004, SPEC-0001, and DOC-0001 contain no
competing whitespace disposition. They were reviewed without revision.
Historical evidence that records an earlier raw PASS, finding, failure, or
incident remains historical evidence and was not rewritten.

## 6. Policy Decision

`git diff --check` remains the authoritative mandatory detector for the entire
publication boundary. It is not the sole authority for the engineering
disposition of every reported byte pattern.

File-type-aware qualification is required. A zero exit is a whitespace PASS.
A non-zero exit is preserved and normally blocks, except when every finding is
individually proven to be a permitted two-space Markdown hard break and no
protected finding exists. In that case whitespace qualification passes with
recorded formatting findings.

This decision does not weaken exact publication membership, digest, controlled
document, semantic, cross-reference, repository, registry, package, EOS, or
integrated-platform validation.

## 7. Controlled-Document Revisions

- PROC-0001 Version 1.18 candidate records raw validator status separately
  from an explicitly governed classification.
- PROC-0005 Version 1.6 candidate establishes the authoritative diff and
  whitespace qualification policy.
- PROC-0006 Version 1.4 candidate delegates publication whitespace
  classification to PROC-0005 and reconciles its header with the existing
  Version 1.3 revision-history baseline.

No standard, specification, index registration, lifecycle state, approval
state, persistence state, or publication plan was changed.

## 8. Cross-Reference Reconciliation

PROC-0001 already relates to PROC-0005 and PROC-0006. PROC-0005 already relates
to PROC-0001 and PROC-0006 and conforms to SPEC-0001. PROC-0006 already relates
to PROC-0001 and PROC-0005. The new normative text uses those existing
ownership relationships and introduces no duplicate authority.

DOC-0001 continues to resolve all three canonical procedure paths and does not
encode their version values. No index change is required. The complete review
and revision disposition is recorded in the companion change matrix.

## 9. Recovery Impact Assessment

`git diff --check HEAD^ HEAD` for PU-01A exits 2 and reports 11 lines in six
Markdown evidence files. Each reported line contains exactly two ASCII
terminal spaces after non-whitespace metadata content. No blank-line
whitespace, three-or-more-space sequence, tab hard break, non-Markdown
trailing-space finding, space-before-tab error, or conflict marker was
reported.

Under the corrected policy, those 11 lines are permitted Markdown hard breaks
when reviewed as the intentional line separation between adjacent metadata
fields. The PU-01A commit remains intact and is a valid recovery point.

ZH-PUBLICATION-EXECUTION-003 remains a truthful record: its mandatory command
did return 2 and the execution correctly stopped under the policy then
available. This correction does not rewrite that incident or retroactively
claim that execution continued. A new execution handoff may reassess the
post-PU-01A boundary using the corrected policy and, if every other boundary
condition passes, resume before PU-02.

## 10. Risks

- A broad Markdown exception would hide accidental padding; the policy
  therefore permits only an exact, reviewed two-space hard break.
- Raw command status could be lost if wrappers report only an aggregate
  disposition; PROC-0001 and PROC-0006 now require both values.
- Generated Markdown may reproduce accidental whitespace indefinitely; its
  exception requires a controlled format contract and deterministic output.
- The corrected procedures are working-tree candidates and do not themselves
  authorize publication or resume.
- Future tooling may automate classification, but this handoff authorizes no
  tooling implementation.

## 11. Final Recommendation

Accept the reconciled procedure correction as the single qualification policy
for whitespace validation of controlled publication artifacts. Keep
publication paused after PU-01A. Preserve PU-01A and
ZH-PUBLICATION-EXECUTION-003, and require a new publication execution handoff
before any boundary reassessment, PU-02 activity, synchronization, push, or
remote verification.
