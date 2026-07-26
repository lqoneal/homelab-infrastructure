# ZEUS-P2-014 Production Authority Authorization

Authorization reference:
`ZEUS-P2-014-PRODUCTION-AUTHORITY-AUTHORIZATION`

Date: 2026-07-26
Owner: Lawrence O'Neal
Production principal: `loneal`
Decision: `AUTHORIZED`

Lawrence O'Neal designates
`/home/loneal/.ssh/id_ed25519` as the production principal key for `loneal`
and authorizes the same key to establish the initial production enrollment
trust root.

Public-key fingerprint:
`SHA256:UNx/JS4jk1ojyF8X2PvWjFnhqtx9vaiovuAmU02txZo`

This authorization permits:

- publication of the public key in the enrollment allowed-signers file;
- configuration of `loneal` as the enrollment authorization principal;
- preparation and detached signing of the Lawrence O'Neal / `loneal`
  enrollment request;
- application of that request through the repository owner-enrollment
  interface;
- compilation and controlled installation of the resulting production trust.

It does not bypass signature verification, trust compilation, publication
readiness, or explicit activation.
