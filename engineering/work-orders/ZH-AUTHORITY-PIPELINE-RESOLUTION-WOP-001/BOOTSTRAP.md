# Authority Pipeline Resolution WOP Bootstrap

Mission ID: `ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001`

This package implements Gates A–G of the approved Authority Pipeline
Resolution plan. It does not authorize OA-06 implementation or acceptance,
OA-07 work, publication, push, deletion, or fabrication of authority.

## Start or resume

1. Work only from `/data/engineering/repositories/homelab`.
2. Run `SCRIPTS/verify-package`. Stop if integrity fails.
3. Record resolved root, filesystem device/inode, Git common directory,
   branch, remote, HEAD, upstream, worktrees, and porcelain status.
4. Read `STATE.json`. Verify its recorded HEAD is an ancestor of or equal to
   current HEAD and compare its working-tree digest. Unexplained changes stop
   the gate; expected durable WOP changes are reconciled in evidence.
5. Find the first gate whose durable conditions are not complete. Verify the
   intended condition before doing work. If already satisfied, record
   `PREVIOUSLY_COMPLETED` evidence and do not repeat it.
6. Execute `EXECUTION-ORDER.md` in order. A later gate never repairs a failed
   prerequisite by weakening it.
7. Before every modifying operation, read its rollback section and capture
   pre-state. Preserve append-only evidence and authority history.
8. After each operation, write evidence, update the gate checkpoint, reconcile
   affected records, and atomically update `STATE.json`.
9. Stop at any operator, publication, irreversible, missing-authority, or
   design-conflict boundary.

Verification is always performed before mutation and again afterward. Tests
use temporary repositories and may not publish. Shadow compatibility output is
diagnostic only. No layer except EWI may emit a terminal initiation decision.

Mission closeout requires all Gate A–G exit criteria and a non-dispatching EWI
qualification. Close with
`AUTHORITY_PIPELINE_RESOLUTION_VERIFIED_AWAITING_OPERATOR_ACCEPTANCE`,
`OA-06 = BLOCKED_PENDING_SEPARATE_OPERATOR_RESUME_AUTHORIZATION`, and
`OA-07 = INELIGIBLE`.

