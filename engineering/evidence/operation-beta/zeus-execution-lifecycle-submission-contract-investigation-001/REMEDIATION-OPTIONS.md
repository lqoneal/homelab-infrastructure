# Submission Contract Remediation Options

## Option 1 — Canonicalize before submission

Require the operator to use structured Phase-1 authoring and submit only an
`ADMISSION_READY` output with its immutable traceability sidecar.

**Strengths:** clear boundary, strong provenance, small P2 surface, easy replay
and fail-closed validation.

**Risks:** the repository has no supported identity-preserving promotion
command; using the current structured authoring command would derive a new
hash-based identity. It adds operator work and could tempt manual sidecar
creation.

**Assessment:** correct long-term authoring discipline, but insufficient as the
immediate remediation for this already-authored lifecycle source.

## Option 2 — Automatic canonicalization at `zeus submit`

Resolve and fully classify a valid Development source, then construct its
canonical Phase-1 provenance deterministically before entering P2. Preserve
source bytes, source digest, declared WOP/Mission identity, and all semantic
gates. Treat a legacy admission record as a separate explicit compatibility
input.

**Strengths:** preserves the public source-only `zeus submit <SOURCE>`
workflow; removes silent route switching; supports identity-preserving
promotion; provides one submission receipt, one admission request, and replay
semantics.

**Risks:** requires a rigorous promotion contract and tests for provenance,
identity, package creation, route conflicts, and legacy migration. Automatic
canonicalization must not fill unknown authority or gate values.

**Assessment:** preferred, provided promotion is a real validated boundary,
not a synthetic sidecar shortcut.

## Option 3 — Converge Stage 1 itself

Keep source-driven Stage 1 as the canonical new-WOP path and remove obsolete
generic authority requirements from its legacy callers.

**Strengths:** reuses the existing Development authority snapshot and
receipt-backed lifecycle; smaller immediate change for the no-argument source
path.

**Risks:** does not solve the `--repository` route guard; leaves P1/P2 and
Stage-1 semantics competing; keeps two submission receipts and two lifecycle
entry contracts; makes provenance behavior depend on invocation shape.

**Assessment:** not sufficient as the authoritative target. Stage 1 should
remain the package-intake/derived lifecycle owner beneath the normalized
submission contract.

## Option 4 — New parallel submission system

Add a separate lifecycle submission lookup or authority table for this mission.

**Assessment:** reject. It violates the repository's one-resolver and
identity-preservation direction, increases migration risk, and would create a
new competing authority source.

## Decision

Adopt Option 2, combined with an explicit classifier and a compatibility guard.
The result is one canonical path for new Development WOPs, one explicit legacy
adapter for historical records, and no generic approval dependency for work
explicitly authorized by a submitted WOP.
