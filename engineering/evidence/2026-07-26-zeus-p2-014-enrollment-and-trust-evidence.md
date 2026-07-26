# ZEUS-P2-014 Production Enrollment and Trust Evidence

Date: 2026-07-26
Result: PASS

## Authorization root

- Owner and authorization principal: Lawrence O'Neal / `loneal`
- Authorization reference:
  `ZEUS-P2-014-PRODUCTION-AUTHORITY-AUTHORIZATION`
- Key fingerprint:
  `SHA256:UNx/JS4jk1ojyF8X2PvWjFnhqtx9vaiovuAmU02txZo`
- Signature namespace: `zeus-owner-enrollment`

## Enrollment

- Request ID:
  `OWNER-ENROLLMENT-3efbed4d-2a40-51ee-8431-f166f3d269b9`
- Canonical request SHA-256:
  `468a810b4e80f962b7a533ad2b99c5ed57eda5a970c7c921bc90a59b528c842d`
- Enrollment ID:
  `OWNER-IDENTITY-c32bd3bc-9dc9-563f-95e3-11aa7e7d3f4e`
- Lifecycle: `active`
- Registry revision: `1`
- Registry digest:
  `34564b809340d0c7efc85ef9e125756471d5edb5be212db8b962401eabd629c8`
- Registry digest valid before enrollment: yes
- Registry digest valid after enrollment: yes
- Trust compilation ready: yes

The byte-exact detached signature verified as `loneal` before the repository
owner-enrollment interface applied the request.

## Preserved rejected signatures

Two earlier signatures are preserved as negative-path evidence:

- `ZEUS-P2-014-loneal-enrollment-request.pretty-json.sig` covered formatted
  JSON and was rejected by the canonical verifier.
- `ZEUS-P2-014-loneal-enrollment-request.canonical-newline.sig` covered
  canonical JSON plus a terminal newline and was rejected by the byte-exact
  canonical verifier.

Neither rejection modified the registry.

## Trust compilation

Candidate trust was compiled through `authority-ownerctl compile-trust` and
verified to contain:

- exactly one owner: Lawrence O'Neal;
- exactly one principal: `loneal`;
- the enrolled ED25519 public key;
- the source registry digest shown above;
- signature namespace `zeus-authority-publication`.

The verified candidate was installed into the repository-fixed production
trust policy and allowed-signers file. No private key entered the repository.
