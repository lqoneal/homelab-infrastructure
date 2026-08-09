# Live Projection Trace

The transition sequence was verified before and after each mutation:

```text
AWAITING_EXECUTION_DISPATCH
  -> INVOKE_PROVIDER
  -> provider acknowledgement: READY_FOR_EXECUTION_START
  -> START_EXECUTION
  -> execution session: READY_FOR_CONTROLLED_EXECUTION
  -> BEGIN_CONTROLLED_MISSION_WORK (STOP)
```

All eight mission-native surfaces and `zeus status --json` agreed after the
final transition on Mission ID, WOP ID, provider ID, dispatch ID, provider
session ID, invocation ID, execution ID/session ID, no blockers, and the next
action. Current operands were resolved from the durable runtime, repository,
EOS, mission, WOP, and provider projections; no current-state literal was
introduced.
