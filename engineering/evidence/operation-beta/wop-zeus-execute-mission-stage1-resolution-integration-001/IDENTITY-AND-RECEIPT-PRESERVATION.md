# Identity and Receipt Preservation

Preserved bindings are the Stage 1 transaction identity, receipt admission identity, execution identity, package digest, source digest, authority snapshot digest, provider selection, dispatch receipt, and predecessor receipt lineage. The resolver uses the execution receipt identity when present and otherwise the existing Stage 1 transaction identity; it never generates a replacement transaction, admission, provider, dispatch, or receipt.

The promoted package digest is `814361acbc225619ade3614a5c8027a06bb5c0ca1ed3fbd0b49e93ce86c3f94f`; its source digest is `0b41100481802772007df28f41fee9a7c195d81f2e9c30f42799218c3a3da8f`.
