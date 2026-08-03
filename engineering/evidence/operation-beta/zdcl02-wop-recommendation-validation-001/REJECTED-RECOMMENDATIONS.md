# Rejected Recommendations

The following proposals are rejected for this WOP and may not be smuggled in
through implementation details:

1. **Live provider launch or live mission dispatch — REJECT.** Explicitly
   prohibited by the source WOP and outside the planned ZDCL boundary.
2. **Autonomous mission selection or execution — REJECT.** Would expand
   authority and contradict the fail-closed controlled lifecycle.
3. **Codex-only execution architecture — REJECT.** Conflicts with provider
   neutrality and the published temporary-compatibility status of `engctl
   codex`.
4. **Direct `engctl codex` authority — REJECT.** PROC-0001 states the wrapper
   is orchestration/notification metadata, not an authority gate.
5. **New authority layer, provider registry, or controlled-document class —
   REJECT.** Existing owners must be reused; SPEC-0014 requires burden of
   proof for foundational additions.
6. **Publication, EOS synchronization, commit, push, merge, tag, or closeout
   in this WOP — REJECT.** The source itself sets the unpublished review
   boundary.
7. **Using pending placeholders as admission evidence — REJECT.** A
   resolver-produced, digest-bound result is required before admission.
