# Canonical Repository and Noncanonical State Resolution Plan

Mission: `ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001`

Status: planning proposal only; no tree, projection, runtime record, or archive
was changed or retired.

## 1. Canonical topology

```text
/data/engineering/repositories/homelab     AUTHORITATIVE WORKING TREE
    |
    +--> /data/engineering/eos             generated/runtime EOS state
    +--> /data/engineering/shared          transfer/generated/qualification artifacts
    +--> /data/engineering/staging         transfer and isolated staging
    +--> /data/engineering/recovery        immutable recovery archives
    +--> /data/engineering/wops            legacy external WOP tree (retire/migrate)
    +--> .zeus/runtime                     local runtime state derived from repository inputs
```

Read-only inspection found one registered Git worktree for Homelab:
`/data/engineering/repositories/homelab`, on `main`. The only other Git
repository found under `/data/engineering/repositories` is `SprinterOS`,
which is a different project and is out of Homelab consolidation scope.

The external `/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP` is a legacy,
independently mutable package tree with approvals, verification records,
scripts, state, and backups. It overlaps
`engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001` and is therefore the
highest-risk duplicate. It must be frozen read-only, compared by manifest and
semantic identity, preserved as evidence where necessary, then retired. It
must not be used to resume OA-06.

## 2. Noncanonical-state justification matrix

| Location | Content | Owner | Class | Reason external | Producer / update direction | Validation | Rebuild | Retention / retirement |
|---|---|---|---|---|---|---|---|---|
| `/data/engineering/eos/state` | EOS identity, manifest, project projection, pointers | EOS synchronization/checkpoint services | derived plus small runtime pointers | operator-wide runtime view cannot be only a Git document | canonical repo -> EOS; pointer by explicit checkpoint selection | `repository-eos-authority.yaml`, digest/content comparison | run synchronization from canonical repo; preserve runtime pointer policy | retain while EOS operates; never hand-edit projections |
| `/data/engineering/eos/runtime` | operational state and repository inventory cache | engctl runtime | derived cache | fast cross-repository status | canonical observations -> cache | regenerate-and-compare, schema validation | delete/rebuild atomically from observed canonical repos | retain as disposable cache |
| `/data/engineering/eos/checkpoints` | commit/project checkpoint metadata | EOS checkpoint service | append-only runtime evidence | checkpoints represent operational time/selection | canonical identity -> append-only checkpoint | commit existence, repo identity, schema/digest | cannot recreate historical time; can rebuild current checkpoint | retain per declared policy; archive then expire |
| `/data/engineering/state` | storage baseline configuration | platform storage owner | runtime configuration | host/platform path configuration is environment-specific | explicit operator configuration, not repo projection | schema/path allowlist and ownership | restore from separately controlled platform config | retain if consumed; otherwise migrate config template to repo and retire |
| `/data/engineering/shared` | mission packages, generated docs, qualification transfer material | producing service/operator | transfer/generated | interchange and external qualification outputs | canonical -> generated/transfer; never reverse merge | manifests, signatures, expiry, source commit/digest | regenerate from canonical source when reproducible | TTL by artifact class; archive evidence, expire transfer copies |
| `/data/engineering/staging` | archives and unpacked WOP002 workspaces | staging service/operator | transfer staging | temporary intake/isolated qualification | input -> staging; accepted changes enter repo only by explicit reconciliation | archive digest, traversal/link checks, source manifest, TTL | restage from source archive | quarantine then delete after TTL and evidence preservation |
| `/data/engineering/recovery` | bundles, patches, snapshots, tar archives | recovery service/operator | immutable archive | recovery copies must survive working-tree loss | canonical snapshot -> archive only | SHA256SUMS, restore drill, source metadata | not derived; restore is controlled reconciliation | retain per recovery policy; expire only after replacement backup verification |
| `/data/engineering/wops/ZEUS-OA-PROGRESSIVE-WOP` | overlapping OA package, approvals, scripts, verification/state | legacy OA tooling/operator | obsolete duplicate pending forensic classification | no continuing valid reason once repository package is authoritative | currently independently editable (prohibited); freeze immediately | compare every file/digest/semantic record against repository WOP and accepted receipts | none; repository is source after migration | preserve unique historical evidence, then retire entire live tree |
| canonical `.zeus/runtime/authority` | active pointer and append-only authority generation | authority publication runtime | runtime selector/publication | activation must not change the Git baseline it authorizes | repository publications -> explicit activation -> runtime | pointer/artifact manifest/signatures/digests | reactivate a valid repository-prepared generation; never reconstruct authority | retain active/history per authority retention; prune only by approved archival policy |
| canonical `.zeus/runtime/mission-admissions` and Stage 1 state | admission/runtime instances | Admission/Stage 1 services | runtime records | create-only and interruption-safe operational state | canonical WOP + explicit submission -> runtime | schema/digest/idempotency checks | replay only from authoritative inputs where contract permits | retain through mission/reconciliation retention |
| canonical `engineering/runtime/pmct/runs` | qualification evidence | PMCT | evidence/runtime history | potentially large run evidence | canonical candidate -> run output | COMPLETE marker, manifest, artifact hashes | rerun produces new evidence, never overwrites history | archive by qualification policy |

Unknown home-directory clones or inaccessible locations are not proven absent
by this filesystem-scoped scan. Gate A must inspect configured mounts, Git
worktree registries, process working directories, service configuration, and
operator-declared locations before asserting global uniqueness.

## 3. Consolidation procedure

1. Record canonical identity: resolved root, remote URL, object format, current
   branch/HEAD, worktree list, and filesystem identity.
2. Freeze independent Homelab editing outside the canonical root through
   permissions/service configuration and an operator notice. Do not delete.
3. Inventory every path named by EOS configuration, environment files,
   services, cron/systemd jobs, shell history configuration, WOP scripts, and
   runtime pointers. Capture file manifests, ownership, modes, symlinks, Git
   metadata, and open writers.
4. Classify each location using the matrix above. Quarantine ambiguity;
   absence of a documented producer/owner/rebuild path is a retirement signal.
5. For every duplicate, compare repository-relative identities, content
   digests, structured IDs, timestamps, and receipt types. Unique records are
   imported only through an explicit reconciliation plan; no bulk reverse
   synchronization is permitted.
6. Convert retained consumers to canonical paths or one-way projection APIs.
   Remove write capability from projections. Make generated files carry
   source repository ID, commit/tree digest, generator version, and generation
   timestamp.
7. Rebuild EOS from `engineering/eos/repository-eos-authority.yaml`; validate
   byte-identical output for unchanged inputs. Preserve checkpoint/runtime
   records separately.
8. Reconcile Project State, Work Registry, PMCT, Stage 1, EENS, Progressive
   state, and resume status by IDs/digests. Repository records prevail for
   authored state; external operational facts enter only via typed,
   append-only reconciliation receipts.
9. Move obsolete trees to a read-only quarantine/archive, retain manifest and
   provenance, redirect/disable writers, observe for a full retention window,
   then delete only under separate retirement authorization.

## 4. Drift prevention

Prevention controls, not merely alarms:

- canonical-root allowlist enforced in `engctl`, Zeus, EWI, WOP tooling,
  publication tools, and service units before any write;
- refuse a Homelab write when `git rev-parse --show-toplevel`, remote identity,
  and configured canonical path do not all agree;
- one registered Homelab worktree policy for protected operations; test
  worktrees must live in ephemeral paths, carry a test marker, and be
  incapable of publication;
- projections mounted/readable as read-only to users and regenerated via one
  service account/API;
- no bidirectional file synchronization; reverse reconciliation accepts typed
  receipts, never copied source files;
- active writer registry and exclusive locks for runtime stores;
- generated manifests bind source commit/tree digest and generator version;
- package indices replace filename guesses and require exactly one current
  record;
- CI/preflight scans known roots, Git common-dir/worktree metadata, service
  configurations, active processes, untracked external files, and source
  digests before protected initiation;
- external locations have TTL, owner, retention class, and retirement
  condition enforced by inventory.

Detection must fail closed on multiple active roots, divergent Homelab Git
histories, projection edits, stale generation manifests, untracked
authoritative-looking external files, remote mismatch, or canonical/derived
drift. The diagnostic names the path, owner, expected direction, source
digest, observed digest, and corrective procedure.

## 5. Retirement acceptance

A duplicate is retirement-ready only when it has no active writer or consumer;
all unique material is classified and preserved or explicitly rejected; a
manifest and restore reference exist; canonical consumers pass without it;
monitoring observes no access for the required interval; and an authorized
retirement action names the exact path. This plan performs none of those
retirement actions.
