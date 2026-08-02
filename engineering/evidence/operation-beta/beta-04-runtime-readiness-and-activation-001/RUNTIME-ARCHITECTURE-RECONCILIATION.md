# Runtime Architecture Reconciliation

Runtime paths are centralized in `scripts/lib/emp/runtime_paths.py`. The
default preserves writable installations; `ZEUS_RUNTIME_ROOT` supports a
read-only repository mount without silently relocating state. Controllers load
canonical sources without writes; mutation paths retain atomic stores,
symlink rejection, and fail-closed behavior. No capability implementation was
added.
