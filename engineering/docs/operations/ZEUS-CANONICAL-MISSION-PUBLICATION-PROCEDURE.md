# Zeus Canonical Mission Publication Procedure

After a Development publication WOP is qualified, Zeus resolves its immutable
target linkage. Publication approval, synchronized EOS, and passing platform
validation are mandatory before activation. Activation creates exactly one
active Mission Contract, one Beta registry work item, and one digest-bound
operational package binding.

Before publication, `zeus mission show STOPQ-01 --json` reports blocked
canonical discovery with the Development transaction and next action. After
publication, the same command family must report exactly one active contract,
registry entry, package, authority, blocker set, and next action.
