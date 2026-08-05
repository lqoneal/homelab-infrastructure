# Revert Plan

Preserve the accidental commit, verify the preservation ref, run normal
`git revert 8ee6b1f`, amend only its message to identify this corrective WOP,
push `main`, compare its effective tree with `55147d9`, then synchronize EOS.
No reset, force push, deletion, or candidate republish is permitted.
