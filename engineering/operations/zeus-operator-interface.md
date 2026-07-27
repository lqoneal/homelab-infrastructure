# Zeus Operator Interface

For Zeus Operational Alpha, the operator is Lawrence O'Neal and the production
principal is `loneal`. The authenticated Zeus CLI is the authoritative
interface through which Lawrence O'Neal exercises engineering authority,
subject to repository policy and runtime validation. Controlled documentation
remains the normal operational source of execution authority. Zeus does not
gain independent authority from the session and does not invent approval
records.

## Global launcher

The repository-controlled launcher manager installs a per-user symbolic link to
the authoritative executable. It never installs into a privileged path and
never replaces an unrelated entry.

```text
scripts/install-zeus-launcher install
scripts/install-zeus-launcher verify
command -v zeus
zeus --help
```

`~/.local/bin` must already be present in `PATH`. Repeated installation accepts
an exact existing link without rewriting it. A regular file, broken link, link
to another target, or other conflicting entry fails closed.

Rollback is:

```text
scripts/install-zeus-launcher remove
```

Removal is idempotent and removes only the exact link owned by this repository.
It refuses to remove a conflict.

## First-100-invocation orientation

The operator-interface record is separate from engineering orchestration:

`<repository>/.zeus/runtime/operator-interface-state.json`

Schema version 1 contains exactly `schema_version`, `invocation_count`, and
`orientation_limit`. The limit is 100. The store uses an exclusive file lock,
atomic replacement, deterministic JSON, mode `0600`, a mode-`0700` runtime
directory, strict field/type/version validation, and symbolic-link rejection.
It is intentionally separate because the orchestration schema is strict and
operator education is neither mission state nor an authority source.

A qualifying invocation is any normal invocation against the repository-
authoritative runtime, including bare invocation, `--help`, `intro`, `status`,
valid commands, invalid commands, and argument parse failures. Counting occurs
once before argument parsing or execution. Invocation 1 through invocation 100
display orientation; invocation 101 does not. Manual `zeus intro` is a genuine
invocation and therefore counts, but remains available after the limit.

Explicit engineering state overrides (`--state` or `ZEUS_STATE`) do not count
and do not initialize or modify operator-interface state. Tests use
`ZEUS_TESTING` plus `ZEUS_OPERATOR_STATE` to isolate their state; these are
engineering test controls, not supported alternate operational locations.
Normal automation counts because it is indistinguishable from a genuine
operator request at the CLI boundary. Use `ZEUS_NO_INTRO=1` to suppress text
for one invocation; suppression still increments the count and never resets it.

Orientation is emitted to `stderr` before help, parsing, or command execution.
Machine-readable command output remains exclusively on `stdout`, so
`zeus status | jq .` remains valid while orientation is active.

Review and inspect the interface with:

```text
zeus intro
zeus intro --status
ZEUS_NO_INTRO=1 zeus status
```

Bare `zeus` prints concise help and exits successfully without performing work.
Unsupported natural language does not become unrestricted engineering
instruction.

## Operating mode and next action

`zeus next-action` is the read-only production-facing decision interface. It
resolves repository identity and HEAD, published baseline, configured
authority, dispatcher activation, production agent registration and
qualification, PMCT state, current gate, current-binding operator verification
and acceptance, active Zeus work authority, and blocking conditions. It
selects the first unmet prerequisite; it does not
activate, publish, qualify, register, dispatch, or otherwise perform the
reported action.

Lifecycle precedence is repository identity, operational authority, current
published baseline, current-binding gate verification, matching operator
acceptance, then the next gate's WOP pre-execution verification. Dispatcher
state cannot outrank an unsatisfied operator gate boundary. For OA-01, the
post-publication sequence is:

```text
verification absent -> RUN_OA-01_VERIFICATION
verification PASS and acceptance absent -> RECORD_OA-01_OPERATOR_ACCEPTANCE
verification and acceptance current -> RUN_OA-02_PRE_EXECUTION_VERIFICATION
```

The last result is conditional evaluation, not OA-02 execution or dispatcher
commissioning authority.

Here, read-only means that the command does not modify repository content,
orchestration state, authority, publication, dispatcher, agent, qualification,
PMCT capability, dispatch, promotion, or resume state. Like every normal Zeus
invocation, it may perform exactly one bounded presentation-history mutation:
atomically incrementing `invocation_count` in
`.zeus/runtime/operator-interface-state.json`. It may also acquire and create
the adjacent empty lock file needed to serialize that increment. No other
runtime mutation is permitted for `next-action`.

The operator-interface record is non-authoritative presentation history. It is
not an input to next-action resolution or any authority, publication,
dispatcher, agent, qualification, dispatch, promotion, PMCT-result, or resume
decision. Its only behavioral effect is whether the first-100-invocation
orientation text is emitted to `stderr`; it cannot change the decision object
or its digest. A normal invocation that changes any field other than the
monotonic `invocation_count`, changes any authoritative state, or creates any
other durable record violates this command contract.

```text
zeus next-action
zeus next-action --json
```

Human output includes stable machine-readable footer fields. `--json` emits
the complete schema-versioned decision and deterministic decision digest.

`ZEUS_MODE=BETA` means feature implementation, qualification, PMCT, and
read-only production inspection are permitted within their separate authority
while production safeguards remain active and Operational Alpha is incomplete.
`ZEUS_MODE=PRODUCTION` is reserved for a future promotion decision after the
published baseline matches, dispatcher is active, a qualified production
agent exists, every PMCT gate passes, and no blocker remains. This interface
cannot promote the operating mode.

## Gate verification and approval

The normal human gate lifecycle is:

```text
zeus approve OA-XX
zeus verify OA-XX
zeus approve OA-XX
```

The first approval invocation resolves the authoritative PMCT PASS run,
qualified repository HEAD, evidence digest, and WOP manifest digest. It prints
the exact verification command and exits without requesting approval.
Candidate resolution requires the run manifest to match the current repository
HEAD, implementation baseline, published baseline, and active authority
publication. Historical PASS runs remain preserved but cannot become
ambiguous candidates for a newer authority binding.

Verification checks repository identity and tracked cleanliness, the exact
PMCT result and manual-review contract, evidence integrity and completion,
WOP integrity and resume status, and the next-gate acceptance blocker. It
creates a checksummed verification record but never records acceptance or
executes another gate.

The second approval invocation accepts only a matching verification record,
prints the bound gate, run, HEAD, verification, and acceptance state, then
requests `Approve OA-XX? [y/N]:`. Only `y` or `yes` records acceptance.
`--yes` is reserved for controlled automation and retains every integrity and
binding check.

`bin/record-operator-approval` is an internal persistence primitive. Operators
do not locate or provide run IDs, evidence paths, repository hashes, or
receipt paths manually.

Approval receipts are append-only and versioned by gate and binding. The first
receipt for a gate may remain at the legacy flat path; successors are created
under `operator-approvals/OA-XX/`. Every successor records the exact path and
SHA-256 digest of its predecessor. Historical receipts remain append-only,
read-only audit evidence and never authorize a different HEAD, PMCT run, or evidence digest.
Eligibility accepts only a checksummed receipt bound to the current HEAD.

## Corruption recovery

Read, validation, lock, or write failure stops the invocation with exit 78.
Zeus never silently resets corrupt or incompatible state. Preserve the failed
file, investigate it, and restore a known-good whole-file backup while Zeus is
idle. If no trustworthy backup exists, move the corrupt record aside manually
under operator control, invoke Zeus to initialize a new empty interface record,
and retain the old record as incident evidence. This procedure affects only
orientation history; it does not alter orchestration state or authority.
