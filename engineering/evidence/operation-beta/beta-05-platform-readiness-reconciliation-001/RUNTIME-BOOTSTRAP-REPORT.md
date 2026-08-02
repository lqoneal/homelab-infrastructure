# Runtime Bootstrap Report

Status: PASS

Authority was resolved from the published Operational Alpha authority model and BETA-04 authority chain, not session provenance.

Both `/data` and `/` are read-only ext4 mounts. The documented `/var/lib/zeus-runtime/homelab` and repository-local roots therefore cannot be written; Unix ownership was not the cause. The canonical mutable root is `/home/loneal/.local/state/zeus/homelab`, selected with `ZEUS_RUNTIME_ROOT`.

Bootstrap created schema-version-1 state and returned `READY`. Replay returned `created: false` with the same state digest `41e4ed25d5ec357dd1c6247b0693af4d3d207f8494a77a736a90225a42f19807`. Published authority, staged submission, admission, execution, and append-only evidence records were copied byte-for-byte from the legacy read-only runtime; the new orchestration state was preserved. Status passed with BETA-04, executable mission `NONE`, and no runtime error or banner.
