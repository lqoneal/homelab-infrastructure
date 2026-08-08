# Operational Bootstrap Runtime Reconciliation

The authoritative current runtime contract is the repository-bound user-state
runtime selected by `scripts/lib/emp/runtime_paths.py`:

`/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57`

Repository-local `.zeus/runtime` content is historical or explicit legacy
compatibility state unless adopted through the native runtime operation. The
old repository-fixed location assertion was therefore stale.

The `--state` option remains an isolated engineering/test orchestration-state
override. Its status route must not require the historical OA
`authority/active-publication.json` pointer, which is not required by the
canonical P2/P3/P4 lifecycle. The CLI now returns the overridden orchestration
state projection directly for that route. Canonical mission authority and
submission state remain on the durable runtime path.

The missing `active-publication.json` is not restored by copying or creating an
ad-hoc artifact. It remains a legacy OA projection and is not a prerequisite
for canonical lifecycle discovery.
