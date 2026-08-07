# Runtime Enforcement Changes

- `scripts/lib/eos/convergence_runtime.py`: resolves submitted-WOP authority,
  accepts historical field names as provenance, retains scope/action checks,
  preserves explicit WOP approval gates, reports WOP/mission/scope/lifecycle/
  admission/blockers/next-action/baseline/EOS/session fields, and no longer
  requires a policy-backed generic Authority Record for submitted-WOP work.
- `scripts/lib/emp/wop_admission.py`: approval is optional by default and is
  enforced only when an approval block/gate is declared by the WOP.
- `scripts/lib/emp/wop_schema.py` and `wop_packaging.py`: generic approval and
  authority-node metadata are optional compatibility fields; package intake
  requires the immutable WOP reference and does not synthesize a second grant.
- `scripts/lib/emp/stage1_runtime.py`: Stage 1 records submission authority as
  `operator-submitted WOP`, preserves integrity checks, and keeps provider,
  baseline, repository, dispatch, and receipt controls.
- `scripts/lib/emp/codex_adapter.py`: managed start/resume/stop and controlled
  work no longer require generic operator approval; explicit execution blockers
  and approvals still fail closed. The managed package declares
  `workspace-write`, immutable mission/WOP/provider/session bindings, and no
  missionless writable path.
- `scripts/lib/eos/context.sh`: inspected; no authority gate was present and
  no change was required.
