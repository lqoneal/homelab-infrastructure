# Replay Evidence

An isolated transaction was prepared and preverified twice with unchanged
inputs. The second call returned PASS with `replayed=true`, retained
`PREPUBLICATION_VERIFIED`, retained `prepublication_result=PASS`, exposed only
`STAGE_PUBLICATION_CANDIDATE`, and preserved the original receipt path and
digest. The completed milestone occurred exactly once and the Git index
remained empty.

A simulated transaction-write failure left a valid receipt without a
transaction reference. Fresh status continued to reproduce
`CANDIDATE_ISOLATED -> VERIFY_PREPUBLICATION`; it did not expose staging.
Receipt retry logic reuses a valid matching receipt and rejects any conflict.

