# Runtime Portability Report

The runtime path contract is repository identity plus the resolver precedence: explicit command line, `ZEUS_RUNTIME_ROOT`, repository configuration, user-state default, then system configuration. Qualification uses an isolated resolver-selected root and does not encode a user-specific path.

`rg '/home/loneal' scripts --glob '*.py' --glob '*.sh' --glob 'zeus'` returns no executable-code matches.
