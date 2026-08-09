# Root-cause analysis

The native controller's previous `_manifest_paths` helper scanned candidate
manifest filenames and returned the first path list it could parse. Markdown
prose, historical evidence, unrelated Operation Beta manifests, and current
mission manifests were therefore not separated by live Mission/WOP authority.
When no first-match manifest was usable, the controller correctly returned an
empty candidate, but it had no canonical resolver capable of explaining why.

The corrective adds one read-only authority resolver. It starts from the live
canonical lifecycle projection, binds the active WOP, discovers manifests only
under evidence relationships carrying the exact identity, validates
qualification/publication state, expands directory entries, and computes the
deterministic union of exact paths. The existing transaction controller remains
the sole owner of transaction state and publication mutation.

The resolver deliberately distinguishes already-published paths from new
paths through Git's live object/tree and diff projections. It does not select a
path because it is dirty, similar in name, or in an evidence directory.
