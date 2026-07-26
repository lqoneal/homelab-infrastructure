# ZEUS-P2-004 Operational Authority Publication Qualification Evidence

Date: 2026-07-26
Baseline: `5ebaa32` plus ZEUS-P2-002/P2-003 working-tree implementation
Result: PASS — publication and activation framework qualified

## Qualification boundary

Qualification used ephemeral Ed25519 keys, an isolated trust policy, signed
test envelopes, an isolated transaction directory, and an isolated activation
target under `ZEUS_TESTING=1`. No qualification key, private key, approval,
authority record, or activated source was published into production state.

The repository-fixed trust policy remains
`operationally_configured: false`, its owner map is empty, and its allowed
signers file contains no keys.

## Proven workflow

The automated qualification:

1. generates an ephemeral signing key;
2. enrolls owner-specific principals in an isolated allowed-signers file;
3. externally signs one envelope for every required owner record;
4. stages create-only envelope and signature copies;
5. rebuilds the candidate entirely from verified envelopes;
6. verifies completeness, dependencies, exact Git baseline, authority DAG,
   approval scope, lifecycle, identity, provenance, and ARS acceptance;
7. confirms the staged candidate remains disabled;
8. explicitly activates an isolated source and records an activation receipt;
9. proves the Authority Resolution Runtime accepts the activated source;
10. rolls back to byte-identical prior state; and
11. independently exercises signed revocation without deleting history.

Authorization Decision Record publication is also staged and owner-verified,
while correctly remaining outside the pre-WOP required activation set.

## Negative cases

| Case | Expected result |
| --- | --- |
| Missing required record type | readiness rejected |
| Wrong owner for record type | staging rejected |
| Unauthorized/tampered signature | staging/readiness rejected |
| Staged envelope modified after staging | readiness signature verification rejected |
| Repository baseline mismatch | ARS readiness rejected |
| Repository production trust policy unconfigured | framework construction rejected |
| Staged but not explicitly activated | runtime rejects `operationally_configured: false` |
| Rollback active/source digest mismatch | rollback rejected |
| Revocation not bound to activation | revocation rejected |

## Owner enforcement

| Record | Required owner |
| --- | --- |
| Mission, phase, work item | Mission Registry |
| Repository identity and baseline | Repository Identity Management |
| Authority node | Governance Authority Graph Registrar |
| Approval | Engineering Governance decision registry |
| ADR | Authorization Decision Service |
| Identity | Identity Provider |
| Governing baseline | Engineering Governance Baseline Registrar |
| Operational configuration/revocation | Mission Admission Controller |

The publication tool has no signing operation and accepts no production trust
policy override.

## Commands

```text
python3 scripts/tests/test-authority-publication.py
python3 scripts/tests/test-authority-resolution-runtime.py
python3 scripts/tests/test-conversational-reasoning.py
python3 scripts/tests/test-emp-registry.py
python3 scripts/validate_controlled_documents.py
python3 scripts/tests/test-controlled-document-relationships.py
bash scripts/verify.sh
git diff --check
```

Aggregate results are recorded in the completion report.
