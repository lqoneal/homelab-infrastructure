# ZEUS-P2-021 Runtime Mutation Engineering Assessment

Date: 2026-07-26
Implementation baseline: `9944595f715e3c1d60b457e498f3277b68baaa40`
Disposition: Option B — retain and explicitly bound presentation-history write

## Finding

Normal `zeus next-action` execution intentionally participates in the
first-100-invocation orientation mechanism qualified by Zeus P1. It increments
only `invocation_count` in
`.zeus/runtime/operator-interface-state.json`. This is non-authoritative
presentation history, not repository, orchestration, authority, publication,
dispatcher, agent, qualification, dispatch, PMCT-result, promotion, or resume
state.

## Source and call path

1. `/home/loneal/.local/bin/zeus` is a symbolic link to `scripts/zeus`.
2. `scripts/zeus:main()` collects arguments and determines whether an
   engineering-state override is active.
3. For a normal invocation it constructs
   `scripts.lib.emp.operator_interface.OperatorInterfaceStore`.
4. Before argument parsing and command dispatch, `main()` calls
   `OperatorInterfaceStore.increment()`.
5. `increment()` obtains an exclusive `flock`, validates the runtime path and
   existing schema, increments `invocation_count`, and calls `_save_locked()`.
6. `_save_locked()` writes deterministic JSON to a mode-0600 temporary file,
   fsyncs it, atomically replaces the state file, and retains mode 0600.
7. `scripts/zeus` then parses `next-action` and calls
   `scripts.lib.emp.next_action.resolve_next_action(ROOT)`.

## Information and purpose

Schema version 1 contains exactly:

```text
schema_version
invocation_count
orientation_limit
```

Only `invocation_count` changes. `schema_version` remains 1 and
`orientation_limit` remains 100. The counter decides whether Zeus emits the
operator-orientation text to `stderr` for invocations 1 through 100. This
behavior is explicitly specified and qualified by the P1 operator-interface
contract; it is not an audit ledger, authorization receipt, or operational
telemetry input.

## Decision influence

The operator-interface file is read only by
`scripts/lib/emp/operator_interface.py` and the associated operator-interface
tests/status presentation. Repository search found no consumer in:

- `scripts/lib/emp/next_action.py`;
- authority resolution or publication;
- dispatcher or production execution;
- agent registration or qualification;
- mission admission or execution;
- PMCT classification or capability state;
- project resume or orchestration decision logic.

At the orientation threshold the counter can change only whether explanatory
text appears on `stderr`. It does not change `next-action` stdout, structured
JSON, authoritative fields, selected action, result, or decision digest.
PMCT invokes `next-action` and therefore can increment the counter, but PMCT
does not inspect the counter and cannot derive a capability result from it.

## Safety classification

Permitted for normal `zeus next-action`:

- one monotonic increment of `invocation_count`;
- atomic replacement of the same operator-interface state file;
- lock acquisition and creation of the adjacent empty lock file.

Prohibited:

- repository-content changes;
- changes to schema version or orientation limit;
- orchestration, authority, publication, dispatcher, agent, qualification,
  PMCT capability, dispatch, promotion, or resume-state changes;
- creation of approval, evidence, transition, execution, or reconciliation
  records;
- any mutation selected by or dependent on the next-action decision.

## Recommendation

Retain the write and adopt Option B. The behavior is deliberate, bounded,
non-authoritative, and already part of the qualified P1 invocation contract.
Removing it only for `next-action` would create an exception to the rule that
every normal invocation counts and would make orientation history dependent on
command selection.

The P2-021 command contract must use the precise term “authoritative-state
read-only” and disclose the one permitted presentation-history mutation.
Verification must prove both sides of the boundary: Git and authoritative
state remain byte-for-byte unchanged, while the counter advances by exactly
one and no other operator-interface field changes.

The telemetry assessment is accepted in principle. Operational Alpha WOP
execution remains suspended because OA-01 independent operator verification is
pending and operator acceptance is not recorded. OA-02 is blocked by
`OA-01_OPERATOR_ACCEPTANCE_REQUIRED`.

## Validation

The bounded-runtime verification observed counter `610` advance to `611`,
while repository HEAD, Git status, the five authoritative next-action inputs,
and `.zeus/runtime/orchestration-state.json` remained byte-for-byte unchanged.
The command, counter-shape, and authoritative-immutability checks all exited
zero.

Targeted validation:

```text
python3 scripts/tests/test-zeus-operator-interface.py
11 tests; PASS; exit 0

python3 scripts/tests/test-zeus-next-action.py
2 tests; PASS; exit 0

python3 -m py_compile scripts/zeus scripts/lib/emp/operator_interface.py scripts/lib/emp/next_action.py
PASS; exit 0
```

Repository validation:

```text
for test_file in scripts/tests/test-*.py; do python3 "$test_file"; ...; done
SCRIPT_TEST_FAILURES=0

engineering/tests/zeus-operational-alpha/tests/run-tests.sh
PMCT_SELF_TEST_RESULT=PASS

python3 scripts/tests/test-emp-registry.py
EMP Work Registry tests passed.

python3 scripts/validate_controlled_documents.py
Controlled-document checks passed: 2578
Controlled-document checks failed: 0

git diff --check
PASS
```

OA-01 revalidation:

```text
PMCT_RUN_ID=PMCT-20260726T220148Z-042c4ea4c6a3
PMCT_GATE=OA-01
PMCT_RESULT=PASS
ZEUS_PROGRESSIVE_TEST_RESULT=PASS
PMCT_EVIDENCE=/data/engineering/repositories/homelab/engineering/runtime/pmct/runs/PMCT-20260726T220148Z-042c4ea4c6a3
PMCT_COMPLETION_MARKER=COMPLETE
```

`sha256sum -c artifacts.sha256` verified all twelve hashed artifacts, and the
`COMPLETE` marker comparison passed.
