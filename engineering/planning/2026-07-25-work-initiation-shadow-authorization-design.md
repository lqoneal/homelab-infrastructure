# Engineering Work Initiation Shadow Authorization

Date: 2026-07-25
Status: Operational observation; legacy authorization remains exclusive
Mission: Zeus Operational Alpha Mission G

## Integration

`eos_platform_qualify` now performs two independent evaluations. The existing
qualification is named the legacy evaluation and retains its exact exit status.
After it completes, the shadow adapter consumes the Mission D Authority Engine,
Mission E WOP model and Mission F compatibility evaluator. Shadow failure,
denial, disagreement or evidence-persistence failure cannot alter the legacy
exit status.

The integration applies to every `engctl platform qualify` invocation and every
direct use of the canonical EOS Work Initiation qualification function.

## Inputs

Shadow inputs are explicit environment configuration:

- `EOS_SHADOW_AUTHORITY_GRAPH`
- `EOS_SHADOW_WOP`
- `EOS_SHADOW_STATE`
- `EOS_SHADOW_RECEIPT`
- optional `EOS_SHADOW_LEASE` and `EOS_SHADOW_REVOCATION`
- optional `EOS_SHADOW_EXPECTED_AUTHORITY`
- optional deterministic `EOS_SHADOW_EVALUATION_TIME`

Missing or malformed input produces a `VALIDATION_FAILURE` Zeus decision and an
ADR. Repository state, EOS state, resume state and derived records are recorded
only as observations and never supplied as authority.

## Evidence retention

Authorization Decision Records are canonical JSON stored by default under
`$(eos_runtime_dir)/authorization-decisions`. `EOS_SHADOW_ADR_DIR` may select an
isolated qualification directory. Evaluation identity is UUIDv5 over canonical
decision, repository and timestamp material. Exclusive creation prevents an
existing record from being overwritten; an identical replay is idempotent and
a collision with different bytes fails.

The decision digest covers legacy and Zeus results, authority chain,
capabilities, requested effects, WOP identity and the Mission F input digest.
Identical canonical evaluations therefore yield identical records and digests.

## Disagreement handling

The comparison engine emits:

- `NONE`
- `LEGACY_ALLOW_ZEUS_DENY`
- `LEGACY_DENY_ZEUS_ALLOW`

The first divergent decision point is retained. In every case,
`enforcement_authority` remains `LEGACY`, `shadow_only` remains true, and the
shell function returns only the legacy result. No WOP is executed, no session
is created, and no live lease is acquired.
