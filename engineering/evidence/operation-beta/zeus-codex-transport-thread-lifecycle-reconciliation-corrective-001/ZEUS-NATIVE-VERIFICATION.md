# Zeus-Native Verification

After correction, the live read-only surfaces agree:

- `zeus codex status`: `THREAD_RECOVERY_BLOCKED` /
  `RECONCILE_CODEX_THREAD_RECOVERY`
- `zeus mission next`: `READY_FOR_CONTROLLED_EXECUTION`, readiness
  `CODEX_RECOVERY_REQUIRED`, same next action and blocker
- `zeus mission recovery`: same next action and blocker
- `zeus codex reconcile <MISSION>`: same read-only classification and action
- `zeus codex attach <MISSION>`: refuses the stopped managed transport and
  reports the same action
- `zeus codex resume ... --approve`: fails with
  `THREAD_RECOVERY_BLOCKED` before transport launch

The Zeus wrapper and all mission/WOP/execution/provider/repository bindings
remain intact. Mission and repository work remain false. Help for
`codex resume` describes transport replacement, native same-thread resume,
fail-closed no-fallback behavior, and explicit fork semantics.

The unrelated `mission recommend` Operational Alpha dependency and valid-Beta
`mission explain` lookup defect are recorded as deferred; neither shares this
transport/thread root cause and neither was changed.
