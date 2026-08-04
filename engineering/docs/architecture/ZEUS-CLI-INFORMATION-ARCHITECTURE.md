# Zeus CLI Information Architecture

The public command hierarchy follows operator intent:

* Authoring: `zeus wop format|template|init|validate|lint|inspect|explain`
* Execution: `scripts/zeus submit <wop>` and `scripts/zeus resume <mission>`;
* Exceptional execution control: `scripts/zeus stop <mission>`;
  status, next-action, and `zeus mission ...` are read-only projections.

`stop` is an exceptional, fail-closed control for an active or plausibly hung
execution. Zeus verifies the recorded process identity and process group,
requests graceful termination, escalates after a bounded timeout when needed,
preserves evidence, and leaves the mission `INTERRUPTED` with
`scripts/zeus resume <mission>` as the next action. It does not cancel the
mission, change authority, or create a replacement transaction.
* Diagnosis and verification: `zeus doctor` and `zeus platform verify`
* Administration: `zeus runtime`, `zeus config`, and `zeus synchronize`

Command ownership is intentionally distinct: top-level `zeus verify <GATE>`
remains governed gate verification, while `zeus mission verify <MISSION_ID>`
is mission-scoped. `zeus platform verify` is a read-only integrated check and
never authorizes, submits, adopts, packages, or synchronizes work. `zeus
synchronize` reports readiness and prints the established `engctl` action; it
does not mutate EOS.

The recovery candidate is classified by `zeus doctor` as `READY_FOR_REVIEW`
when all local checks pass and only publication to `main` and EOS convergence
remain. `READY`, `READY_FOR_PUBLICATION`, `BLOCKED`, and `FAIL` retain their
distinct meanings in the Doctor specification.

The WOP source document remains canonical. Administration projections are
read-only unless a command explicitly states that it mutates state. Default
output is concise; `--json`, `--verbose`, and `--debug` expose detail from the
same canonical result object.
