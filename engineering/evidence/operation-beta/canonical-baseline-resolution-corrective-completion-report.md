# Canonical Published-Baseline Resolution Corrective

Status: `AWAITING_OPERATOR_REVIEW`

## Root cause

Pre-corrective evidence was:

```text
EXPECTED_BASELINE=149252f1806058c9dac765b3718948a82840a592
ACTUAL_VALUE_USED_BY_MISSION_VERIFY=df7fcd9a42e87a8bf09722a903dfb3753d60d856
VALUE_SOURCE=scripts/lib/emp/mission_verification_controller.py:PUBLISHED_BASELINE
FAILURE_BRANCH=verify(): repository_data.current_baseline != PUBLISHED_BASELINE
```

`platform verify` already compared live `HEAD` with `origin/main` and EOS
`EOS-STATE.md:repository_commit`. Mission verification incorrectly treated the
immutable mission artifact baseline as the current publication.

## Corrective design

`scripts/lib/eos/canonical_baseline.py` now owns read-only baseline resolution.
It resolves `HEAD`, `origin/main`, EOS, canonical repository identity, runtime
binding, and optional mission provenance ancestry. Platform verification and
mission verification consume this result. The mission report distinguishes:

```text
CURRENT_PUBLISHED_BASELINE=149252f1806058c9dac765b3718948a82840a592
MISSION_PROVENANCE_BASELINE=df7fcd9a42e87a8bf09722a903dfb3753d60d856
MISSION_BASELINE_RELATIONSHIP=ANCESTOR
PUBLICATION_PARITY=PASS
EOS_BASELINE_PARITY=PASS
RUNTIME_REPOSITORY_BINDING=PASS
```

## Post-corrective evidence

```text
scripts/zeus platform verify       => PASS
scripts/zeus mission verify ...    => PASS
mission_verification                => PASS
read_only                           => true
blockers                            => []
next_authorized_action              => EVALUATE_EXECUTION_PROVIDER
```

The JSON contract contains `current_baseline`, `published_baseline`,
`eos_baseline`, `mission_provenance_baseline`, and
`mission_baseline_relationship` under `repository`.

## Tests and safety

The focused resolver suite covers equal, ancestor, unrelated, missing, and
current publication cases. Existing controller, runtime-discovery, authority,
submission, admission, bootstrap, platform synchronization, Registry, syntax,
and `git diff --check` validations remain required. Repository, EOS, runtime,
and mission artifacts were read-only throughout; no lifecycle mutation,
provider selection, dispatch, execution, publication, or EOS synchronization
was performed.

## Completion markers

```text
CANONICAL_BASELINE_RESOLUTION_CORRECTIVE_COMPLETE
CURRENT_PUBLISHED_BASELINE=149252f1806058c9dac765b3718948a82840a592
MISSION_PROVENANCE_BASELINE=df7fcd9a42e87a8bf09722a903dfb3753d60d856
MISSION_BASELINE_RELATIONSHIP=ANCESTOR
PUBLICATION_PARITY=PASS
EOS_BASELINE_PARITY=PASS
RUNTIME_REPOSITORY_BINDING=PASS
MISSION_PROVENANCE=PASS
PLATFORM_VERIFY_BASELINE=PASS
MISSION_VERIFY_BASELINE=PASS
BASELINE_RESOLVER_CONVERGENCE=PASS
ZEUS_MISSION_VERIFICATION=PASS
READ_ONLY_VERIFICATION=PASS
OPERATION_BETA_AUTHORITY=PASS
OA_AUTHORITY=SUPERSEDED
PROVIDER_SELECTION=NOT_PERFORMED
DISPATCH=NOT_PERFORMED
EXECUTION=NOT_PERFORMED
STOP_BOUNDARY=REACHED
```
