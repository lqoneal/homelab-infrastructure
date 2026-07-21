# Engineering Event & Notification System

The Engineering Event & Notification System (EENS) provides durable,
agent-neutral engineering lifecycle events and notification delivery.

EENS persists events in SQLite, supports ordered replay and durable
consumer checkpoints, and delivers pending notifications through ntfy.

## Current Capability

- Durable SQLite event storage
- Ordered event replay
- Idempotent event persistence
- Durable consumer checkpoints
- Engineering handoff lifecycle events
- Wrapped-command lifecycle events
- One-shot ntfy notification delivery
- Long-running ntfy notification service
- systemd user-service deployment

## Repository Layout

```text
config/       Environment configuration template
docs/         Project documentation
runtime/db/   Event and consumer checkpoint databases
scripts/      Installation and removal scripts
src/eens/     Python application package
systemd/      systemd user-service unit
tests/        Automated test suite
```

## Runtime Contract

The current deployment expects:

- Linux with systemd user services
- Python 3.13
- Execution account: `loneal`
- Repository: `/home/loneal/data/engineering/eens`
- Virtual environment: `/home/loneal/data/engineering/eens/.venv`

The service unit uses absolute paths. Update the unit before relocating
the repository.

## Command-Line Interface

```bash
cd /home/loneal/data/engineering/eens
PYTHONPATH=src .venv/bin/python -m eens --help
```

Run the long-running notification service manually:

```bash
PYTHONPATH=src .venv/bin/python -m eens service ntfy
```

Run one notification-delivery cycle:

```bash
PYTHONPATH=src .venv/bin/python -m eens notify ntfy
```

## Configuration

The installed user service reads:

```text
~/.config/eens/eens.env
```

Supported environment variables:

```bash
EENS_DB_PATH=/home/loneal/data/engineering/eens/runtime/db/eens.sqlite3
EENS_NTFY_SERVER=https://ntfy.sh
EENS_NTFY_TOPIC=your-topic-name
# EENS_NTFY_TOKEN=your-access-token
```

`EENS_NTFY_TOPIC` must be configured before starting the service.

Protect token-bearing configuration files:

```bash
chmod 600 ~/.config/eens/eens.env
```

## Install the User Service

```bash
./scripts/install-user-service.sh
nano ~/.config/eens/eens.env
systemctl --user enable --now eens-notify.service
```

The installer preserves an existing environment file and does not
automatically enable or start the service.

## Service Operation

```bash
systemctl --user status eens-notify.service
systemctl --user restart eens-notify.service
systemctl --user stop eens-notify.service
systemctl --user start eens-notify.service
journalctl --user -u eens-notify.service -n 100 --no-pager
journalctl --user -u eens-notify.service -f
```

## Boot Startup

Enable user lingering so the service can run without an active login:

```bash
sudo loginctl enable-linger loneal
loginctl show-user loneal -p Linger
```

Expected result:

```text
Linger=yes
```

## Diagnostics

```bash
PYTHONPATH=src .venv/bin/python -m eens health
PYTHONPATH=src .venv/bin/python -m eens count
systemctl --user cat eens-notify.service
systemd-analyze --user verify systemd/eens-notify.service
```

## Live Notification Test

After starting the service, emit a qualification event:

```bash
PYTHONPATH=src .venv/bin/python -m eens emit \
  engineering.test \
  --source mission-4-qualification \
  --subject eens-notify-service \
  --idempotency-key mission-4-live-notification-1 \
  --payload '{"message":"Mission 4 live notification test"}'
```

Confirm delivery on the configured ntfy topic and inspect the journal.

## Upgrade Procedure

```bash
cd /home/loneal/data/engineering/eens
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
./scripts/install-user-service.sh
systemctl --user restart eens-notify.service
systemctl --user status eens-notify.service
```

## Uninstall

```bash
./scripts/uninstall-user-service.sh
```

The uninstall script removes the installed unit but preserves:

```text
~/.config/eens/eens.env
```

## Security

- The service runs without root privileges.
- `NoNewPrivileges=true` is enabled.
- `PrivateTmp=true` is enabled.
- ntfy access tokens must not be committed.
- The installed environment file should use mode `0600`.

## Development Verification

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
bash -n scripts/install-user-service.sh
bash -n scripts/uninstall-user-service.sh
git diff --check
```
