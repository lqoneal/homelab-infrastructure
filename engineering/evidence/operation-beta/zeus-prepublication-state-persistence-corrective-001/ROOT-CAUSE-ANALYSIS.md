# Root Cause Analysis

The durable transaction was correct, but transaction-bound `inspect()` and
`status()` replaced its next action with `_revalidate_authority()` output.
That cohort/candidate revalidation helper returned
`STAGE_PUBLICATION_CANDIDATE` whenever frozen candidate authority was still
valid, regardless of `current_state`. Thus a read model independently skipped
the durable `PREPUBLICATION_VERIFIED` transition.

The full path was:

```text
scripts/zeus publication status/inspect
  -> publication_transaction.status()/inspect()
  -> _load_transaction(): CANDIDATE_ISOLATED, VERIFY_PREPUBLICATION
  -> _revalidate_authority(): candidate/cohort PASS
  -> helper next-action hint: STAGE_PUBLICATION_CANDIDATE
  -> status/inspect overlay replaces transaction next action
  -> mission_projection()/CLI can expose the overrun read model
```

`publication verify` itself ran validators and called `_record_milestone()`,
which created a receipt and saved the transaction. However, that path returned
without an explicit authoritative reload/integrity proof, preverification was
mislabelled `read_only`, and persistence errors were not publication-typed.
An interrupted receipt-first write could leave an orphan receipt that was not
replay-safe because receipt reconstruction used a new timestamp.

A second independent enforcement defect existed in `stage()`: its allowed
states included `CANDIDATE_ISOLATED`. Even after fixing display logic, a direct
stage request could therefore bypass preverification. Mission projection and
resume also consumed stored or independently projected next-action values
instead of one integrity-aware transaction resolver.

Root-cause classifications: status projection independently computing the next
action; read-only path leaking authorization; milestone precondition defect;
missing post-persistence reload validation; and incomplete orphan-receipt
replay/failure handling. The defect was not a cohort identity error and was
not corrected by changing cohort authority.

