# Prepublication Validation Root Cause

Stage 2 rendered the EOS projection from the checked-out candidate `HEAD`, although EOS is intentionally the projection of published `main`. Stage 4 then compared operational state and checkpoints directly to the candidate `HEAD`. A valid clean candidate was therefore reported as synchronization drift.

The corrective introduces `scripts/lib/eos/validation_lifecycle.py` as the shared classifier. It proves branch state, local/remote parity, cleanliness, ancestry from `origin/main`, and EOS/checkpoint parity with published `main` before classifying `UNPUBLISHED_CANDIDATE`.
