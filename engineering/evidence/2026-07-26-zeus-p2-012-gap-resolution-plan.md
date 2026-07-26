# ZEUS-P2-012 Gap Resolution Plan

Date: 2026-07-26
Status: Revised by ZEUS-P2-013; deterministic plan only; no commissioning effects

## Dependency-ordered plan

1. The enrollment authorization authority publishes its authentic principal,
   public key, and controlled authorization into
   `engineering/authority/enrollment-allowed-signers`, and controls the update
   of `enrollment-root-policy.yaml` to configured state. This is an external
   bootstrap prerequisite; the toolkit cannot perform it.
2. Lawrence O'Neal supplies the owner-controlled public key for principal
   `loneal` and a valid enrollment authorization reference. The toolkit
   prepares one unsigned enrollment request. Lawrence O'Neal signs it in the
   `zeus-owner-enrollment` namespace, after which the registrar applies it
   through `authority-ownerctl apply-enrollment`.
3. After the `loneal` enrollment is active, `authority-ownerctl compile-trust`
   produces candidate-only `owner-trust-policy.yaml` and `allowed-signers`.
   Their installation requires a separately controlled repository-supported
   action.
4. The designated owners supply complete payloads and sign the following
   prepared envelopes in the `zeus-authority-publication` namespace:

| Record | Producing owner | Required signed content |
| --- | --- | --- |
| mission, phase, work item | Lawrence O'Neal (`loneal`) | Active lifecycle, links, qualified work revision, approval and authority bindings, scope digest |
| repository identity and baseline | Lawrence O'Neal (`loneal`) | Repository ID, canonical locator, assertion ID, exact 40-character Git baseline |
| authority node | Lawrence O'Neal (`loneal`) | Node, graph path/version, chain, capabilities, resolution digest |
| approval | Lawrence O'Neal (`loneal`) | Authentic operator authority, reference, `GRANTED` decision, decision time, `Active` lifecycle binding, matching scope digest |
| identity | Lawrence O'Neal (`loneal`) | Principal authentication record, authenticated status, session ID |
| governing baseline | Lawrence O'Neal (`loneal`) | Active manifest ID/revision, references, and manifest digest |
| operational configuration | Lawrence O'Neal (`loneal`) | Active mission/work/principal binding and activation policy |

5. Initialize one publication transaction, stage the ten signed envelopes, and
   run `authority-publishctl verify`. Readiness must rebuild the candidate,
   validate owner agreement and dependencies, match the exact Git baseline,
   and pass the real Authority Resolution Runtime.
6. Only a `READY` result permits `authority-publishctl activate`. Activation is
   expected to publish a receipt-bound source with
   `operationally_configured: true`; status must then report
   `commissioning_state: READY`.
7. Generate an operational WOP using the published mission, work-item, and
   principal selectors. Verify its immutable identity, repository assertion,
   governing baseline, approval, authority chain, lack of placeholders, and
   submission eligibility.
8. Submit, admit, and execute only when every runtime prerequisite passes.
   Preserve all lifecycle evidence and stop at the first fail-closed result.

## Inputs that must not be invented

- enrollment authority principal, key, and authorization;
- Lawrence O'Neal's `loneal` principal and public key;
- enrollment authorization references and signatures;
- repository assertion and exact intended activation baseline;
- mission, phase, and qualified work-item records;
- authority graph record and resolution digest;
- granted approval and scope digest;
- authenticated operator principal/session;
- active governing manifest and digest;
- Mission Admission activation policy;
- every detached owner signature.

Until these authentic inputs are supplied by their designated authorities, no
complete unsigned enrollment request or publication envelope can be produced
without fabricating authority data.
