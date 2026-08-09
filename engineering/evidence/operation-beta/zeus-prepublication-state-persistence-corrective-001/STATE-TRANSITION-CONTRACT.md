# State Transition Contract

The only canonical prepublication transition is:

```text
CANDIDATE_ISOLATED
  -- validators PASS --> receipt generated
  -- transaction references receipt digest and persists PASS -->
PREPUBLICATION_VERIFIED
  -- fresh reload validates state, ordering, receipt digest and bindings -->
STAGE_PUBLICATION_CANDIDATE authorized
```

The transaction state resolver owns publication next-action resolution.
Candidate/cohort revalidation may veto an action but cannot advance it.

`PREPUBLICATION_VERIFIED` requires all of these durable facts:

- `prepublication_result=PASS`;
- `current_state=PREPUBLICATION_VERIFIED`;
- one passing milestone reference in `milestones`;
- `PREPUBLICATION_VERIFIED` in `completed_milestones` exactly once;
- `PREPUBLICATION_VERIFIED` absent from `pending_milestones`;
- a canonical runtime receipt path;
- a valid receipt content digest matching the transaction reference;
- matching publication, mission, WOP, cohort, repository, supersession, and
  candidate-input bindings;
- persisted next action matching the durable state;
- successful fresh reload and integrity validation.

Failure of validation, receipt integrity, transaction persistence, reload, or
authority revalidation cannot grant staging. Receipt-first persistence is
intentional: an orphan receipt is safe because only a transaction reference
can make it authoritative. Retry reuses a valid orphan receipt, avoiding
duplicate lineage. `stage()` independently requires the durable milestone and
revalidates it before any Git index operation.

