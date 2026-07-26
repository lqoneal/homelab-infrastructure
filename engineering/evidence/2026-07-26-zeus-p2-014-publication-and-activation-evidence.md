# ZEUS-P2-014 Publication Transaction and Activation Evidence

Date: 2026-07-26
Result: PASS

## Publication transaction

- Transaction ID:
  `AUTHORITY-PUBLICATION-23d37b6d-40af-4241-88c3-9ecd62535faa`
- Repository baseline:
  `8c861f5a94064e98a4ecd7a3178ca53b90c27fa4`
- Owner/signer: Lawrence O'Neal / `loneal`
- Signature namespace: `zeus-authority-publication`
- Signed envelope count: `10`
- Candidate digest:
  `911711077b8abe30626be984aaa42b2103342d579d17e8a3ff2498091fac4a88`
- Record types: mission, phase, work item, repository identity, repository
  baseline, authority node, approval, identity, governing baseline, and
  operational configuration

Every detached signature verified against the repository-fixed production
trust file before staging. Staging also reverified envelope identity, record
ownership, payload digest, signer principal, and signature.

## Readiness

- Readiness: `READY`
- Record-type count: `10`
- Resolution ID:
  `ARB-fdf9e199-2fd7-56da-83ab-782dc2ed7284`
- Activation-bound readiness digest:
  `7e4a151c58de5a2ac0d5081881f7a7b95d18ce708f7f8771eec9889e14a29d63`

The readiness verifier rebuilt the candidate from signed envelopes and invoked
the real Authority Resolution Runtime. Repository identity, exact Git
baseline, authority graph, lifecycle, scope, approval, principal,
authentication record, governing manifest, ownership, and provenance passed.

The transaction directory under
`.zeus/commissioning/ZEUS-P2-014/transaction` is the repository interface's
publication record. The interface emits readiness and activation receipts; it
does not define a separate file named `publication-receipt`.

## Activation

- State: `ACTIVATED`
- Activated at: `2026-07-26T19:44:43.839269Z`
- Activated source digest:
  `43858d9225c77236e91188a2d0344ff94e725cbba92f354646423cd9e90524c1`
- Previous source digest:
  `259e4ed1fa1c4e4b4d0323ba10ea3767b9fa492d2c634533b9e172a586132c6f`
- Activation receipt digest:
  `801e87d3547141eebfbf5c4c9011c8f73c687b4f729a91ccacc76e47f08ef373`

Activation was performed only through `authority-publishctl activate`. The
repository-fixed authority source was not hand-edited.
