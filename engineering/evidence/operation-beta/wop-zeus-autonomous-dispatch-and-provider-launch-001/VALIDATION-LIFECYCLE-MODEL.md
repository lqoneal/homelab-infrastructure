# Validation Lifecycle Model

`PUBLISHED` requires `main == origin/main == EOS == checkpoint` and a clean tree. `UNPUBLISHED_CANDIDATE` requires a clean `prepublication/*` branch, local/remote equality, ancestry from current `origin/main`, EOS/checkpoint equality with `origin/main`, and an intact publication boundary. All other states are classified and fail closed.
