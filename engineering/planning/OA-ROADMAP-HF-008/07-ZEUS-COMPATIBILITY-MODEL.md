# Zeus Compatibility Model

Status: `PROPOSED FUTURE INTERFACE CONTRACT — NON-AUTHORITATIVE`

Zeus is a future consumer of EMM facts, not an authority for their creation. It resolves requested entities through explicit schema/revision negotiation and reports compatibility rather than silently interpreting unsupported facts.

| Zeus behavior | Contract |
|---|---|
| Read | request an entity revision or compatible range; return resolved revision and provenance |
| Verify | expose schema, adoption, digest, qualification, and synchronization status |
| Unsupported version | return a structured incompatibility result with supported ranges and migration reference |
| Mixed repository | operate only on exact compatible references; identify blocking mismatches |
| Upgrade | qualify capability adapter before recording adoption of new major/minor support |
| Rollback | select prior qualified compatible consumer binding; do not alter authoritative metadata |

Intended stable interfaces include `zeus state`, `zeus verify`, `zeus lifecycle`, `zeus capabilities`, `zeus authority`, `zeus mission`, and `zeus gate`. Current implementation-specific commands remain transitional adapters and do not confer authority or acceptance.
