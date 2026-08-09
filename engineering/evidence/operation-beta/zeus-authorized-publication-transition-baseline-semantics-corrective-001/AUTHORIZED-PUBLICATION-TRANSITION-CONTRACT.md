# Authorized Publication Transition Contract

Steady state is valid when `HEAD == origin/main == EOS` and the available EOS
projection is consistent.

`COMMIT_CREATED` is valid only when one repository-bound, unsuperseded
transaction for the same mission/WOP has passing integrity and a valid current
receipt; `commit_id == HEAD`; the receipt parent and all recorded starting
baselines agree; origin/EOS remain at that starting baseline; origin is an
ancestor of HEAD; and branch, runtime, repository, and index bindings pass.

`REMOTE_PUBLISHED` is valid only when its receipt binds the exact commit and
`refs/heads/main`, `HEAD == origin/main == commit_id`, and EOS remains at the
authorized starting baseline.

`EOS_SYNCHRONIZED` is valid only when its receipt binds the transaction commit
and `HEAD == origin/main == EOS == commit_id` with a consistent EOS projection.

Ancestry without a matching transaction and receipt never authorizes
divergence. Status and replay are read-only.

