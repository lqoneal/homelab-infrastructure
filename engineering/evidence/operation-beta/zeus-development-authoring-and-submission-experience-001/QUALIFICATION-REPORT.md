# Zeus Development Authoring and Submission Experience

Status: QUALIFIED as a reviewable uncommitted candidate; publication gates remain
blocked by repository–EOS synchronization on the recovery branch.

## Verified public workflow

```text
cd /data/engineering/repositories/homelab
python3 scripts/zeus wop format
python3 scripts/zeus wop template --wop-id WOP-AUTHORING-001 --mission-id AUTHORING-01 --output /tmp/WOP-AUTHORING-001.md
python3 scripts/zeus wop inspect /tmp/WOP-AUTHORING-001.md --json
python3 scripts/zeus wop template --wop-id WOP-AUTHORING-001 --mission-id AUTHORING-01 --format docx --output /tmp/WOP-AUTHORING-001.docx
python3 scripts/zeus wop inspect /tmp/WOP-AUTHORING-001.docx --json
python3 scripts/zeus wop inspect /tmp/WOP-AUTHORING-001.md --json
python3 scripts/zeus wop explain /tmp/WOP-AUTHORING-001.md --json
```

The generated Markdown and DOCX templates both validate without repository
knowledge or package construction. Validation is read-only. Missing metadata
reports all fields and the exact corrective authoring command.

Disposable submission verification used a fresh runtime and the generated
Markdown source:

```text
tmp=$(mktemp -d)
HOME=$tmp env -u ZEUS_RUNTIME_ROOT python3 scripts/zeus --runtime-root $tmp/runtime submit /tmp/WOP-AUTHORING-001.md --json
HOME=$tmp env -u ZEUS_RUNTIME_ROOT python3 scripts/zeus --runtime-root $tmp/runtime submit /tmp/WOP-AUTHORING-001.md --json
```

Observed results were `CLOSED` followed by deterministic `idempotent_replay:
true`; no manual package, registration, provenance, or runtime configuration
was supplied.

## Qualification evidence

- Schema-driven format and template tests pass.
- Markdown and DOCX extraction tests pass.
- Transactional packaging, failure cleanup, replay, and source preservation pass.
- Runtime discovery and protected-baseline tests pass.
- Combined focused suite: 52 tests passing.
- `git diff --check` passes.
- EOS runtime and Registry validation pass.
- Integrated platform Stage 2 remains blocked because EOS projects `main` while
  this recovery branch is unpublished; no publication or merge was attempted.
