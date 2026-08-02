# Runtime Readiness Report

`/data` is an `ext4` mount with `ro,nosuid,nodev,noatime`; `.zeus/runtime` is
owned by the operator with mode `0700`, and files are `0600`. A write probe
fails with `EROFS`, proving mount state—not permissions—is the cause.

The corrected boundary is explicit `ZEUS_RUNTIME_ROOT`. Read-only controllers
do not create locks or state. Submit, admit, execute, publish, and synchronize
fail closed when the selected root is unavailable. Evidence remains immutable.
