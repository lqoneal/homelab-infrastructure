# Zeus CLI Command Consistency — Conflict Register

Status: PASS; reviewable, uncommitted recovery candidate.

| Commands | Conflict class | Disposition | Canonical owner |
|---|---|---|---|
| `zeus verify <GATE>` / `zeus platform verify` | namespace/semantic | preserve; distinct scopes | governed gate verification / integrated read-only verification |
| `zeus mission verify <MISSION_ID>` / `zeus platform verify` | namespace/semantic | preserve; distinct scopes | mission verification / platform verification |
| `zeus validate` / `zeus wop validate` | semantic/compatibility | preserve; document distinction; WOP form is read-only alias | existing repository validation / shared Development WOP validator |
| `zeus health` / `zeus doctor` / `zeus platform verify` | semantic/output | preserve; distinct scopes | historical health / component diagnosis / integrated consistency |
| `zeus status` / `zeus operation status` / `zeus mission status` | namespace/semantic | preserve; document scope | platform/runtime / operation / mission |
| `zeus synchronize` / `scripts/engctl eos synchronize` | authority/state mutation | preserve; Zeus reports readiness only | established EOS authority remains `engctl` |
| `zeus wop inspect|explain|lint|template|init` / `zeus submit` | authority | preserve; advisory/generative commands never authorize | `zeus submit` is sole Development execution entry point |
| `zeus generate-wop` / source-authored WOP submission | authority/compatibility | preserve as authority-bound compatibility command; not a prerequisite | operator source plus `zeus submit` |

No parser duplicate, alias shadow, positional ambiguity, or incompatible
option reuse was found. The full parser-derived tree is in
`command-inventory.json`.

## Mutation audit

`doctor`, `platform verify`, runtime status/identity, config show,
synchronize, WOP inspect/explain/validate/lint, gate verify, and mission verify
are read-only projections. They do not initialize or adopt runtime, package
sources, create registration/provenance, alter mission state, or synchronize
EOS. Only `runtime adopt` is allowed to mutate runtime binding in this
administrative group; `submit` owns the Development lifecycle mutation.

## Authority source

This candidate relies on the published Operational Alpha / Engineering
Governance authority chain. The current session is not a WOP provenance
marker and does not expand authority.
