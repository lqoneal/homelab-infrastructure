# Qualification Report

The restoration is qualified by source inspection and command regression.
Without `--wop`, gate verification no longer emits the convergence-binding
error; it reports the gate as implementation-required through the existing
Operational Alpha interface. With `--wop`, the convergence resolver remains
unchanged and fail-closed. Mission execution without `--wop` reaches the
existing admission/dispatch readiness checks; with `--wop`, convergence
authority is still mandatory.
