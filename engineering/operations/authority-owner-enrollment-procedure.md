# Authority Owner Enrollment and Publication Preparation Procedure

Date: 2026-07-26
Status: Operational toolkit procedure; controlled adoption pending Governance publication
Mission: ZEUS-P2-006

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
| Enrollment authorization authority | Authorize owner enrollment lifecycle requests with its own enrolled key |
| Designated authority owner | Control its signing key and sign its publication envelopes |
| Enrollment registrar | Verify signed requests and update the public enrollment registry |
| Trust compiler | Produce candidate trust files after all eight owners are active |
| Publication validator | Verify owner envelope signatures and assemble a candidate source |
| Mission Admission | Sign operational configuration and explicitly control activation |

No role inherits another role’s signing authority.

## Bootstrap prerequisite

The enrollment authorization authority must externally publish:

1. an approved authorization principal;
2. its public key in `engineering/authority/enrollment-allowed-signers`; and
3. a controlled update setting
   `enrollment-root-policy.operationally_configured: true`.

The toolkit cannot perform or approve this root bootstrap. Until it occurs,
`apply-enrollment` fails closed.

## Enrollment

An owner generates and retains its key outside the repository. Only its public
key is supplied:

```text
scripts/authority-ownerctl prepare-enrollment \
  --action enroll \
  --owner "Mission Registry" \
  --principal mission-registry-publisher \
  --authorization-reference AUTHORIZED-ENROLLMENT-ID \
  --public-key OWNER.pub \
  --at 2026-07-26T22:00:00Z > REQUEST.json
```

The output is unsigned. The enrollment authorization authority reviews the
owner, principal, fingerprint, authorization reference, and scope, then signs
the exact canonical JSON externally:

```text
ssh-keygen -Y sign -f ENROLLMENT_AUTHORITY_PRIVATE_KEY \
  -n zeus-owner-enrollment REQUEST.json
```

The registrar applies it:

```text
scripts/authority-ownerctl apply-enrollment \
  --request REQUEST.json --signature REQUEST.json.sig \
  --signer ENROLLMENT-AUTHORITY-PRINCIPAL
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

Compilation requires an intact registry digest and at least one active identity
for every designated owner. It emits candidate-only `owner-trust-policy.yaml`
and `allowed-signers`. It never installs them into production.

Review owner separation, principals, fingerprints, lifecycle, authorization
references, and registry digest before a separately controlled installation.

## Publication preparation

Inspect required fields without creating values:

```text
scripts/authority-ownerctl publication-template \
  --record-type approval_authority
```

An owner supplies a completed payload and prepares a canonical unsigned
envelope:

```text
scripts/authority-ownerctl prepare-publication \
  --record-type RECORD-TYPE \
  --record-id RECORD-ID \
  --signer-principal OWNER-PRINCIPAL \
  --payload OWNER-PAYLOAD.yaml \
  --at 2026-07-26T22:00:00Z > ENVELOPE.json
```

The command validates required metadata, selects the fixed owner from the
record-type map, calculates payload digest and deterministic envelope ID, and
does not sign.

The designated owner reviews and signs `ENVELOPE.json` with
`zeus-authority-publication`, then the P2-004 publication procedure stages it.

## Governance approval support

Governance supplies the decision payload. The toolkit only validates it:

```text
scripts/authority-ownerctl validate-governance-approval \
  --payload GOVERNANCE-DECISION.yaml
```

Validation requires authority, reference, explicit `GRANTED` or `DENIED`
decision, decision time, `Active` lifecycle binding, and a 64-character scope
digest. Output includes `approval_generated: false`.

The Governance owner then prepares and signs the publication envelope. No
other owner or operator may fill in or sign the decision.

## Commissioning diagnostics

```text
scripts/authority-publishctl status
```

Diagnostics separately report:

- enrollment-root configuration;
- missing owner enrollments;
- compiled owner trust and signer keys;
- missing prepared envelopes and detached signatures;
- missing Governance approval publication;
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
