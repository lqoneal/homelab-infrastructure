# Operational Alpha Human Verification Guide

Proposal: `OA-ROADMAP-HF-005`
Status: `PROPOSED — NON-AUTHORITATIVE`

## 1. Operator procedure

For each gate, use the controlled per-gate verification guide first. Then run
the read-only lifecycle checks below. These commands inspect status and
evidence; they do not accept a gate or grant mission authority.

The intended long-term public interface is `zeus gate`, `zeus lifecycle`,
`zeus verify`, `zeus authority`, `zeus state`, `zeus capabilities`, and
`zeus health`. Any direct script, runtime-file, or per-gate implementation
command remains a transitional adapter and must identify its intended `zeus`
interface in the applicable guide.

```bash
zeus gate show OA-NN
zeus gate receipt OA-NN
zeus gate evidence OA-NN
zeus explain OA-NN
```

The expected result is one exact gate identifier, a current predecessor
receipt where required, complete evidence bindings, and no active later gate.
Use `zeus resume` only after the gate's documented acceptance action; it must
make exactly the listed successor available. Any missing receipt, mismatched
identity, unexpected later-gate activity, or state different from the table is
fail-closed and must be routed to the named owner rather than inferred.

## 2. Lifecycle Verification by Gate

| Gate | Expected predecessor lifecycle state | Expected state after verification | Expected successor availability | Interpret the command result |
|---|---|---|---|---|
| OA-01 | S00 | S01 | OA-02 | repository observation is exact and integrity-valid |
| OA-02 | S00,S01 | S02 | OA-03 | exactly one effective Authority Record resolves |
| OA-03 | S02 | S03 | OA-04 | contract reproduces from the Authority Record |
| OA-04 | S01,S02,S03 | S04 | OA-05 | every context fact names its owner |
| OA-05 | S04 | S05 | OA-06 | staged mission identity is stable |
| OA-06 | S05 | S06 | OA-07 | snapshot exposes an explicit eligibility reason |
| OA-07 | S06 | S07 | OA-08 | selection binds one snapshot and tie-break |
| OA-08 | S02,S03,S07 | S08 | OA-09 | one immutable, qualified WOP resolves |
| OA-09 | S04,S08 | S09 | OA-10 | WOP admission is typed and current |
| OA-10 | S02,S04,S09 | S09 | OA-11 | lease/revocation facts are bounded and current |
| OA-11 | S04,S09 | S09 | OA-12 | agent qualification binds repository/profile |
| OA-12 | S09 | S09 | OA-13 | selected agent matches all constraints |
| OA-13 | S02,S03,S04,S09 | S09 | OA-14 | candidate exists but no execution started |
| OA-14 | S02,S03,S09 | S10 | OA-15 only on ALLOW | terminal EWI is ALLOW, DENY, or STOP—not an inferred grant |
| OA-15 | S10=ALLOW | S11 | OA-16 | one reservation/fence prevents duplicate dispatch |
| OA-16 | S11 | S11,S12 | OA-17 | durable start precedes the EENS event |
| OA-17 | S11 | S12 | OA-18 | events/checkpoints exist; EENS made no decision |
| OA-18 | S11,S12 | S12 | OA-19 | protected effect stayed paused until exact decision |
| OA-19 | S11,S12 | S13 | OA-20 | evidence is append-only and sealed |
| OA-20 | S13 | S13 | OA-21 | manifest binds the exact authority/contract/WOP/attempt |
| OA-21 | S13 | S14 | OA-22 | qualifier is independent and result is attributable |
| OA-22 | S14 | S20 or successor S02 | OA-23 | correction is bounded; old subject did not re-enter |
| OA-23 | S11 or S18 | S18 | OA-24 | interruption checkpoint/fence is durable |
| OA-24 | S18 | S19 then S11/terminal | OA-25 | recovery revalidated owners and did not repeat uncertain effect |
| OA-25 | terminal facts | S17 | OA-26 | source owners reconcile; EOS only projects directionally |
| OA-26 | S13,S14 | S15 | OA-27 | completion is calculated, not acceptance |
| OA-27 | S15 | S16 | OA-28 | explicit acceptance/rejection binds exact qualified result |
| OA-28 | S16,S17 | S22 | OA-29 | attempt is closed, resources safe, outcome projected |
| OA-29 | S22 | S21 | OA-30 | representative lifecycle includes negative/recovery paths |
| OA-30 | S21 | S23 | separately authorized interface only | candidate is not declaration, baseline, publication, or activation |

## 3. Result interpretation

`S10=DENY/STOP`, rejection, blocked recovery, and a no-work correction are
valid safe outcomes. They do not enable the normal successor even if the gate
receipt exists. A successor subject must have its own identity, authority,
evidence, and gate evaluation. This check is what distinguishes deterministic
progression from a merely functional implementation.
