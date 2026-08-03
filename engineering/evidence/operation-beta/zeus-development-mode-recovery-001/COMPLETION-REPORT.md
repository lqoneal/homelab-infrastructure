# Zeus Development Mode Recovery — Completion Report

Status: reviewable publication candidate; not published or merged.

Recovery authorization: `ZEUS-DEVELOPMENT-MODE-RECOVERY-001`.
Starting baseline: `0462022c3a7f7bf880bfcc651486588de8b4ccb0`.

The canonical `zeus submit <WOP_ID_OR_PACKAGE>` path now recognizes an
explicit Development WOP or Markdown/DOCX source, validates it before writing state, generates
registration and provenance, and persists one deterministic lifecycle in the
existing Stage 1 store. Replay is idempotent and interrupted work resumes from
the last completed phase. Protected Alpha and Beta baselines are checked at
every phase. No CAGF-01 capability implementation is included.

Automatic packaging preserves the source document, generates the canonical
five-file package, validates the generated package before Stage 1 mutation,
and refuses source replacement without explicit supersession.

Transactional packaging invariant: source normalization and complete package
validation occur in an isolated staging directory. Only successful validation
is atomically promoted into `engineering/work-orders`; failed DOCX, Markdown,
metadata, manifest, or promotion paths remove staging and create no package
directory, runtime state, registration, or provenance.

DOCX extraction supports both paragraph metadata and controlled two-column
metadata tables. The retained BETA-07 DOCX is explicit and resolvable; any
future unresolved source is rejected transactionally rather than inventing
authority, scope, or effects.

Runtime discovery is automatic and repository-bound. Exact verified commands:

```text
cd /data/engineering/repositories/homelab
unset ZEUS_RUNTIME_ROOT
HOME=/tmp/zeus-runtime-qualification-001 python3 scripts/zeus status --json
HOME=/tmp/zeus-runtime-qualification-001 python3 scripts/zeus mission explain CAGF-01 --json
HOME=/tmp/zeus-runtime-qualification-001 ZEUS_TESTING=1 ZEUS_OPERATOR=loneal python3 scripts/zeus submit engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP --json
HOME=/tmp/zeus-runtime-qualification-001 ZEUS_TESTING=1 ZEUS_OPERATOR=loneal python3 scripts/zeus submit engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP --json
python3 -c "from pathlib import Path; import json; p=next(Path('/tmp/zeus-runtime-qualification-001/.local/state/zeus-runtime').rglob('runtime-identity.json')); print(json.loads(p.read_text())['repository_id'])"
ZEUS_RUNTIME_ROOT=/data/engineering/repositories/homelab/.zeus/runtime python3 scripts/zeus submit engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP --json || test $? -eq 78
```

The first command selects and initializes the user-state runtime; the second
returns the same deterministic instance with `idempotent_replay: true`. The
repository-local override is rejected as an unsafe protected-baseline path.

## Exact qualification commands

```text
cd /data/engineering/repositories/homelab
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
scripts/engineering-executionctl --repository /data/engineering/repositories/homelab inventory
scripts/engctl eos status homelab
scripts/engctl registry validate
scripts/engctl platform validate homelab
ZEUS_TESTING=1 ZEUS_NO_INTRO=1 ZEUS_OPERATOR_STATE=/tmp/zeus-operator.json ZEUS_STAGE1_STATE=/tmp/zeus-stage1 python3 scripts/zeus submit engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP
ZEUS_TESTING=1 ZEUS_NO_INTRO=1 ZEUS_OPERATOR_STATE=/tmp/zeus-operator.json ZEUS_STAGE1_STATE=/tmp/zeus-stage1 python3 scripts/zeus submit WOP-ZEUS-DEVELOPMENT-MODE-RECOVERY-001
ZEUS_TESTING=1 ZEUS_NO_INTRO=1 ZEUS_OPERATOR_STATE=/tmp/zeus-operator.json ZEUS_STAGE1_STATE=/tmp/zeus-stage1 python3 scripts/zeus submit engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-SOURCE.md --json
ZEUS_TESTING=1 ZEUS_NO_INTRO=1 ZEUS_OPERATOR_STATE=/tmp/zeus-operator.json ZEUS_STAGE1_STATE=/tmp/zeus-stage1 python3 scripts/zeus submit /data/engineering/repositories/homelab/WOP-BETA-07-STRENGTHEN-DEVELOPMENT-MODE-CANONICAL-SPECIFICATION-001.docx --json || test $? -eq 78
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/tests/test-zeus-runtime-discovery.py scripts/tests/test-wop-packaging.py scripts/tests/test-zeus-development-mode-recovery.py
python3 -c "import json,glob; p=glob.glob('/tmp/zeus-stage1/missions/*.json')[0]; v=json.load(open(p)); print(v['registration']['registration_id'], v['provenance']['package_digest'], v['packaging'])"
git diff --check
git diff -- engineering/authority/manual-governance-wop-authority-policy.yaml scripts/lib/emp/stage1_runtime.py scripts/zeus
git status --short --branch
```

The verified fixture submission returned `EMM-DEV-96c63f32a2fd08e144326103`
registration, package digest, repository provenance, and `CLOSED` recovery
state. The repeated submission returns the same identity with
`idempotent_replay: true`. Publication and merge remain an explicit operator
action after review.
## Runtime adoption corrective

The verified legacy runtime is reconciled by Zeus only:

```bash
cd /data/engineering/repositories/homelab
unset ZEUS_RUNTIME_ROOT
python3 scripts/zeus runtime status
python3 scripts/zeus runtime identity
python3 scripts/zeus runtime adopt --dry-run --json
python3 scripts/zeus runtime adopt --json
python3 scripts/zeus runtime adopt --json
python3 scripts/zeus runtime status
python3 scripts/zeus runtime identity --json
python3 scripts/zeus doctor --json
scripts/engctl registry validate
scripts/engctl eos status homelab
git diff --check
```

The first adoption returned `MIGRATED`, the repeat returned
`ALREADY_ADOPTED` with adoption ID `78fd6c222b7ff3f5d48408c7`, and the legacy
runtime remained unchanged. The candidate remains uncommitted and unpublished.

## Submission validation unification corrective

`zeus submit <WOP_ID_OR_SOURCE>` is the sole authoritative Development WOP
validation and execution entry point. It re-parses the source, validates the
canonical schema, validates the generated package transactionally, and only
then initializes runtime state and proceeds through the lifecycle. `zeus wop
inspect`, `zeus wop explain`, and the retained `zeus wop validate` alias are
read-only views over the same validator and are never prerequisites.

Invalid submission reports all missing/conflicting metadata and creates no
package, runtime state, registration, or provenance. Qualification evidence is
at `engineering/evidence/operation-beta/zeus-wop-submission-validation-unification-001/`.

## CLI consistency and prepublication verification

The parser-derived command inventory and conflict register are recorded at
`engineering/evidence/operation-beta/zeus-cli-command-consistency-and-prepublication-verification-001/`.
Top-level `zeus verify <GATE>` and `zeus mission verify <MISSION_ID>` remain
unchanged. Integrated read-only verification is owned by `zeus platform
verify`; `zeus doctor` reports `READY_FOR_REVIEW` for this healthy unpublished
recovery branch. No read-only command initializes runtime, creates a package,
registers provenance, changes mission state, or synchronizes EOS.

Exact commands:

```bash
cd /data/engineering/repositories/homelab
unset ZEUS_RUNTIME_ROOT
zeus doctor --json
zeus platform verify --json
zeus runtime status --json
zeus runtime identity --json
zeus runtime adopt --dry-run --json
zeus wop format
zeus wop inspect /data/engineering/repositories/homelab/WOP-BETA-07-STRENGTHEN-DEVELOPMENT-MODE-CANONICAL-SPECIFICATION-001.docx --json
zeus wop explain /data/engineering/repositories/homelab/WOP-BETA-07-STRENGTHEN-DEVELOPMENT-MODE-CANONICAL-SPECIFICATION-001.docx --json
zeus wop validate /data/engineering/repositories/homelab/WOP-BETA-07-STRENGTHEN-DEVELOPMENT-MODE-CANONICAL-SPECIFICATION-001.docx --json
zeus mission verify CAGF-01
zeus verify GATE-1
scripts/engctl registry validate
scripts/engctl eos status homelab
git diff --check
git rev-parse HEAD origin/main
git status --short --branch
```
