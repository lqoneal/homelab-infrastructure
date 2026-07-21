# EENS Gate 2E — Handoff 2
## ntfy Notification Transport Implementation

**Mission:** Engineering Event & Notification System Operational Alpha
**Gate:** 2E
**Handoff:** 2
**Objective:** Implement and qualify durable ntfy notification delivery from persisted EENS events to the verified iPhone topic.

---

## Execution Rule

Before every command:

1. Inspect the current repository state.
2. Determine whether the intended condition is already satisfied.
3. Do not repeat completed work.
4. Record evidence for completed conditions.
5. Execute only unmet work.
6. Stop on any unexpected result and report it before continuing.

Controlled and existing repository content must be preserved. Do not replace an existing implementation without first verifying its current state.

---

## Verified Starting State

Repository:

```bash
~/data/engineering/eens
```

Known-good baseline commit:

```text
cc5a43b Add durable EENS event consumer
```

Verified capabilities:

- Durable append-only event store
- Event replay
- Durable named consumers
- Per-consumer checkpoint persistence
- Handoff lifecycle producer
- Handoff command runtime
- ntfy connectivity from LOpi
- iPhone subscribed to topic `eng-thaDuke-codex`

Verified ntfy endpoint:

```text
https://ntfy.sh/eng-thaDuke-codex
```

Existing empty scaffolds:

```text
src/eens/notify.py
src/eens/config.py
```

---

# Gate 2E — Handoff 2 Procedure

## Step 1 — Establish Repository State

```bash
cd ~/data/engineering/eens
source .venv/bin/activate

pwd
git status --short
git log --oneline -5
```

Expected:

- Repository root is `~/data/engineering/eens`
- Working tree is clean
- `cc5a43b` is present in recent history

Do not continue if the working tree contains unexplained changes.

---

## Step 2 — Inspect Consumer Checkpoint API

```bash
sed -n '1,320p' src/eens/consumer.py
sed -n '1,260p' tests/test_consumer.py
```

Purpose:

- Confirm how pending events are read
- Confirm how checkpoints are advanced
- Identify the safe delivery pattern
- Prevent checkpoint advancement before successful ntfy delivery

No files are modified in this step.

---

## Step 3 — Inspect CLI Test Structure

```bash
sed -n '1,220p' tests/test_cli.py
sed -n '220,620p' tests/test_cli.py
```

Purpose:

- Preserve existing CLI testing conventions
- Confirm parser and dispatch expectations
- Identify where notification CLI tests should be added

No files are modified in this step.

---

## Step 4 — Implement Notification Transport

Implement `src/eens/notify.py` with:

- `NtfyNotifier`
- Standard-library HTTP transport using `urllib.request`
- Server URL normalization
- Topic validation
- Optional bearer token
- Event-to-notification formatting
- Successful delivery result
- Explicit delivery exception
- No checkpoint mutation inside the notifier itself

Required environment settings:

```text
EENS_NTFY_SERVER
EENS_NTFY_TOPIC
EENS_NTFY_TOKEN
```

Default server:

```text
https://ntfy.sh
```

No default topic.

---

## Step 5 — Integrate CLI

Extend `src/eens/cli.py` with:

```text
eens notify ntfy
```

Arguments:

```text
--consumer
--limit
--checkpoint
--server
--topic
--token
--json
```

Required behavior:

1. Resolve server, topic, and token from CLI arguments or environment.
2. Read pending events for the named consumer.
3. Deliver events in durable sequence order.
4. Advance the consumer checkpoint only after each successful delivery.
5. Stop on the first delivery failure.
6. Return nonzero on failure.
7. Leave the failed event and all later events available for retry.
8. Produce no duplicate notifications after successful checkpoint advancement.

---

## Step 6 — Add Tests

Create:

```text
tests/test_notify.py
```

Test coverage:

- Successful HTTP POST
- Correct endpoint
- Correct message payload
- Optional bearer token
- HTTP failure
- Transport failure
- Event formatting
- No real network access

Extend CLI tests to cover:

- Required topic
- Environment fallback
- Successful delivery
- Checkpoint advancement after success
- Checkpoint preservation on failure
- Stop-on-first-failure behavior
- Retry behavior
- Limit behavior
- Independent consumers
- JSON output where applicable

---

## Step 7 — Static Qualification

```bash
python -m py_compile src/eens/*.py
```

Expected:

```text
No output
Exit status 0
```

---

## Step 8 — Full Automated Qualification

```bash
PYTHONTRACEMALLOC=1 PYTHONWARNINGS=always::ResourceWarning PYTHONPATH=src python -m unittest discover -s tests -v
```

Expected:

```text
All tests pass
No ResourceWarning
No unclosed SQLite connection
No network access from unit tests
```

Stop and correct any failure before continuing.

---

## Step 9 — Emit a Dedicated Live Qualification Event

```bash
PYTHONPATH=src python -m eens handoff started     --mission "EENS ntfy Live Qualification"     --handoff 1     --detail "Gate 2E Handoff 2 live phone delivery test"     --json
```

Record the returned sequence number.

---

## Step 10 — Configure Live ntfy Delivery

```bash
export EENS_NTFY_SERVER=https://ntfy.sh
export EENS_NTFY_TOPIC=eng-thaDuke-codex
unset EENS_NTFY_TOKEN
```

Verify:

```bash
printf 'server=%s\ntopic=%s\n'     "$EENS_NTFY_SERVER"     "$EENS_NTFY_TOPIC"
```

Do not print a token if authentication is added later.

---

## Step 11 — Deliver One Event to the iPhone

Use a dedicated consumer so historical events are not all sent during qualification:

```bash
PYTHONPATH=src python -m eens notify ntfy     --consumer gate-2e-live-qualification     --limit 1     --json
```

Expected:

- Command exits successfully
- One ntfy message is accepted
- One notification appears on the iPhone
- Output identifies the delivered durable sequence

If the dedicated consumer begins at sequence 1, use an explicit checkpoint strategy supported by the implementation to position it immediately before the dedicated qualification event. Do not flood the phone with historical events.

---

## Step 12 — Verify Duplicate Suppression

Run the same command again:

```bash
PYTHONPATH=src python -m eens notify ntfy     --consumer gate-2e-live-qualification     --limit 1     --json
```

Expected:

- No second delivery of the same event
- No duplicate iPhone notification
- Checkpoint remains at the last successfully delivered sequence

---

## Step 13 — Verify Event Store Integrity

```bash
PYTHONPATH=src python -m eens count
git status --short
```

Expected:

- Notification consumption does not change the event count
- Only intended source and test files are modified

---

## Step 14 — Review Changes

```bash
git diff --check
git diff --stat
git diff -- src/eens/notify.py src/eens/config.py src/eens/cli.py
git diff -- tests/test_notify.py tests/test_cli.py
```

Confirm:

- No unrelated changes
- No trailing whitespace
- No duplicate notification architecture
- Checkpoints advance only after delivery success

---

## Step 15 — Commit

```bash
git add     src/eens/notify.py     src/eens/config.py     src/eens/cli.py     tests/test_notify.py     tests/test_cli.py

git diff --cached --check
git diff --cached --stat
```

Commit only after qualification passes:

```bash
git commit -m "Add EENS ntfy notification transport"
```

---

## Step 16 — Final Gate Verification

```bash
git status --short
git log --oneline -5

PYTHONTRACEMALLOC=1 PYTHONWARNINGS=always::ResourceWarning PYTHONPATH=src python -m unittest discover -s tests -v
```

Gate passes only when:

- Working tree is clean
- Commit exists
- Entire test suite passes
- No ResourceWarnings occur
- Live notification was received on the iPhone
- Repeated delivery does not duplicate the notification
- Failed delivery cannot advance a checkpoint

---

# Completion Report Requirements

Report:

1. Starting repository state
2. Files changed
3. Transport behavior implemented
4. Checkpoint safety evidence
5. Automated test result
6. Live iPhone delivery result
7. Duplicate-suppression result
8. Final commit hash
9. Final working-tree state
10. Gate verdict: PASS or FAIL
