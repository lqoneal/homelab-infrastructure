# Authority Owner Enrollment and Publication Preparation Procedure

Date: 2026-07-26
Status: Operational toolkit procedure; controlled adoption pending Governance publication
Mission: ZEUS-P2-006

Production ownership amendment: ZEUS-P2-013. Lawrence O'Neal is the sole
designated owner and `loneal` is the sole production principal for every
authority record type.

## Boundary

This procedure prepares and validates public artifacts. It does not establish
the enrollment authorization trust root, generate private keys, sign for an
owner, create an approval, install production trust, publish operational
records, or activate Zeus.

Private keys remain in owner custody. Only public keys, fingerprints, signed
requests, unsigned publication templates, externally signed envelopes, and
receipts may enter the repository workflow.

## Roles

| Role | Responsibility |
| --- | --- |
| Lawrence O'Neal (`loneal`) | Authenticate the CLI session, control the production key, authorize the enrollment lifecycle request, and sign domain-specific publication envelopes |
| Enrollment registrar | Verify signed requests and update the public enrollment registry |
| Trust compiler | Produce candidate trust files after Lawrence O'Neal is actively enrolled |
| Publication validator | Verify owner envelope signatures and assemble a candidate source |
| Authenticated operator | Sign operational configuration and explicitly control activation |

These are functional roles within one human ownership model. They do not imply
additional people, organizations, committees, or principals. Record and
validation separation remains mandatory even though the roles share one owner.

## Bootstrap prerequisite

Lawrence O'Neal must externally publish:

1. the authorization principal `loneal`;
2. its public key in `engineering/authority/enrollment-allowed-signers`; and
3. a controlled update setting
   `enrollment-root-policy.operationally_configured: true`.

The toolkit cannot perform or approve this root bootstrap. Until it occurs,
`apply-enrollment` fails closed.

## Enrollment

Lawrence O'Neal generates and retains the production key outside the
repository. Only its public key is supplied:

```text
scripts/authority-ownerctl prepare-enrollment \
  --action enroll \
  --owner "Lawrence O'Neal" \
  --principal loneal \
  --authorization-reference AUTHORIZED-ENROLLMENT-ID \
  --public-key OWNER.pub \
  --at 2026-07-26T22:00:00Z > REQUEST.json
```

The output is unsigned. Lawrence O'Neal reviews the owner, principal,
fingerprint, authorization reference, and scope, then signs the exact canonical
JSON externally. The signature records the authenticated human decision; Zeus
does not create it:

```text
ssh-keygen -Y sign -f ENROLLMENT_AUTHORITY_PRIVATE_KEY \
  -n zeus-owner-enrollment REQUEST.json
```

The registrar applies it:

```text
scripts/authority-ownerctl apply-enrollment \
  --request REQUEST.json --signature REQUEST.json.sig \
  --signer loneal
```

The fixed production root policy and registry cannot be overridden. Test
overrides require `ZEUS_TESTING=1`.

## Rotation, suspension, and retirement

Use the same signed request sequence with `--action rotate`, `suspend`, or
`retire`. Rotation requires a new public key and the predecessor enrollment ID.
Suspension and retirement accept no new key and require the active enrollment
ID. Every lifecycle change requires fresh external authorization.

Rotation links predecessor and successor. Suspension and retirement remove the
identity from compiled active trust without deleting history.

## Verification and candidate trust

```text
scripts/authority-ownerctl status
scripts/authority-ownerctl compile-trust --output CANDIDATE-DIRECTORY
```

Compilation requires an intact registry digest and one active `loneal`
identity for Lawrence O'Neal. It emits candidate-only `owner-trust-policy.yaml`
and `allowed-signers`. It never installs them into production.

Review the owner and principal, fingerprint, lifecycle, authorization reference,
and registry digest before a separately controlled installation.

## Publication preparation

Inspect required fields without creating values:

```text
scripts/authority-ownerctl publication-template \
  --record-type approval_authority
```

The authenticated operator supplies a completed payload for each authority
domain and prepares a canonical unsigned envelope:

```text
scripts/authority-ownerctl prepare-publication \
  --record-type RECORD-TYPE \
  --record-id RECORD-ID \
  --signer-principal loneal \
  --payload OWNER-PAYLOAD.yaml \
  --at 2026-07-26T22:00:00Z > ENVELOPE.json
```

The command validates required metadata, selects Lawrence O'Neal as the fixed
production owner, calculates the payload digest and deterministic envelope ID,
and does not sign.

Lawrence O'Neal reviews and signs `ENVELOPE.json` with
`zeus-authority-publication`, then the P2-004 publication procedure stages it.

## Operator approval support

Lawrence O'Neal supplies the decision payload through the authenticated
operator workflow. The toolkit only validates it:

```text
scripts/authority-ownerctl validate-governance-approval \
  --payload GOVERNANCE-DECISION.yaml
```

Validation requires authority, reference, explicit `GRANTED` or `DENIED`
decision, decision time, `Active` lifecycle binding, and a 64-character scope
digest. Output includes `approval_generated: false`.

Lawrence O'Neal then prepares and signs the publication envelope as `loneal`.
Zeus may not fill in, infer, or sign the decision.

## Commissioning diagnostics

```text
scripts/authority-publishctl status
```

Diagnostics separately report:

- enrollment-root configuration;
- missing owner enrollments;
- compiled owner trust and signer keys;
- missing prepared envelopes and detached signatures;
- missing authenticated-operator approval publication;
- empty operational record collections; and
- activation status.

## Recovery and audit

Preserve enrollment requests, detached signatures, authorization references,
fingerprints, registry revisions, candidate trust output, owner payloads, and
publication envelopes. Never preserve private keys.

On registry digest failure or identity disagreement, stop and restore a
verified whole-registry copy. Do not reconstruct authorization history from
compiled trust files.

## Controlled-document disposition

This operational procedure is implementation evidence, not an approved
Governance procedure. Controlled adoption requires a separate Governance
publication and DOC-0001 reconciliation. Existing controlled approvals and
lifecycle metadata are unchanged.
