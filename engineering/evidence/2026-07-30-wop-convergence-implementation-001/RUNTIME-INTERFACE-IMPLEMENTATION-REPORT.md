# Runtime Interface Implementation Report

`engineering/execution/execution-interface.yaml` is schema 3 and pins
SPEC-0005@2.0, PROC-0001@2.0, STD-0003@2.0, TPL-0001@2.0, TPL-0002@2.0, and
SPEC-0014@1.0. It declares the EMM and a dedicated convergence route.

Stable operator commands are `zeus authority resolve --wop ... --revision ...
--action-name ...`, `zeus lifecycle`, `zeus capabilities`, `zeus state`, and
`zeus health`. These commands inspect and resolve; none activates a WOP.
