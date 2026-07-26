# ZEUS-P2-016 Signature Verification Evidence

Date: 2026-07-26
Result: PASS

Both revision-2 envelopes were independently reconstructed as sorted compact
JSON with no trailing newline and verified using:

- namespace: `zeus-authority-publication`
- principal: `loneal`
- key fingerprint:
  `SHA256:UNx/JS4jk1ojyF8X2PvWjFnhqtx9vaiovuAmU02txZo`
- repository-fixed signer registry:
  `engineering/authority/allowed-signers`

Signature SHA-256 values:

- repository baseline:
  `f793928abad5bb97fb3633d2e6621b6b5c0e0d5ab7b8606b1abf197a211353d7`
- repository identity:
  `d51fcece9c5c62578891bdc1b48c03773ddea2be26e3d81f8f2987a11af6c697`

The first baseline signature covered pretty-printed rather than canonical JSON
and was rejected by the publication interface. It is preserved at
`engineering/authority/publications/history/ZEUS-P2-016-rejected/`.
