# ESC-C02-CORRECTIVE-001

This corrective resolves C02-F-027.

It exists because the frozen C02 contract legitimately requires RESULT.yaml
before operator review while the current roadmap controller rejects a result
for a gate that has not yet been marked complete.

This roadmap does not reopen or rewrite C02.

C02 remains historical/current evidence under its frozen contract.

The corrective establishes the generic lifecycle required for all future gates:

CURRENT
→ RESULT_RECORDED
→ AWAITING_OPERATOR_REVIEW
→ ACCEPTED
→ COMPLETE
→ NEXT_GATE_CURRENT

Execution is manual and strictly one CR item at a time.

Current position is always authoritative in `STATE.yaml`.

Do not infer progress from conversation history.
