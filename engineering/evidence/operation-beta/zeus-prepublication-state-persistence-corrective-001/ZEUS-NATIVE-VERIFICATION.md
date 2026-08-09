# Zeus-Native Verification

Starting native verification established repository, origin, and EOS parity at
`e7e48ab6b523d94e73d40fb4311f86bc7118b0b1`, an empty index, and the exact live
publication/cohort identities.

After the controller change, read-only live status derives its action from the
durable transaction rather than the candidate revalidation hint. Because the
controller source is itself one of the frozen 116 candidate paths, the
corrective necessarily changes the candidate content digest. Bound cohort
revalidation therefore reports `STALE_CLASSIFICATION` and the transaction
resolver reports `REPREPARE_PUBLICATION_TRANSACTION`; it does not expose
staging. The frozen digest remains
`7912e25e924e33cb7ba23cbe1590ec68bc135184eceb02cf190cee4b6d9da262`;
the current live candidate digest is
`dc125ce1bff722b5cdb0ec7df362ec303c6f875b44f26a884ef50811498bf126`.

Fresh mission status independently reproduces
`publication_state=CANDIDATE_ISOLATED`, `prepublication_result=null`, and
`publication_next_action=REPREPARE_PUBLICATION_TRANSACTION`. Transaction
integrity remains PASS, proving that the blocker is candidate drift rather
than transaction corruption. Platform and repository/EOS validation remain
PASS at the starting published baseline.

Final authoritative record digests were
`fd705acb9b0542b87a6d366326ce8d84ad2799c564bd1b7b4d6e659a155e87f2`
for the unchanged active transaction and
`6427a48d945c243fdc387fedd4009d3e71726909ca8ccc091703f63d0703b6da`
for the unchanged cohort. The receipt directory still contains only the four
pre-preverification receipts; the prepublication receipt remains absent.

The live `verify-pre` command is not permitted while that frozen digest is
stale. No live milestone, receipt, cohort, transaction, Git index, commit,
remote, or EOS mutation was performed by isolated qualification.
