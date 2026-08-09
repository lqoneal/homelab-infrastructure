# Requirement Coverage Matrix

The matrix maps each ledger requirement to implementation, test, current
controlled documentation, Zeus-native verification, and evidence. “Prior
evidence” means the requirement was completed before this bounded corrective;
it is not being silently re-executed.

| ID | Implementation component | Test/proof | Controlled document | Zeus-native verification | Evidence |
|---|---|---|---|---|---|
| R001 | CAGF identity corrective boundary | deferred/no-execution checks | historical/deferred scope | CAGF not discovered as execution | prior corrective evidence |
| R002 | submission investigation | investigation command records | submission contract docs | lifecycle remains unexecuted | investigation package |
| R003 | canonicalization/P2 boundary | canonicalization and replay suite | WOP submission docs | submission receipt/mission surfaces | canonicalization corrective |
| R004 | superseded by later lifecycle authority | state/prohibition checks | current boundary docs | native pre-provider state | ledger/audit |
| R005 | document/runtime reconciliation | full validation | reconciled controlled corpus | native surface checks | reconciliation package |
| R006 | planning record | plan validation | planning record | lifecycle planning state | roadmap persistence |
| R007 | canonical read model | Wave 1 tests | lifecycle read-model docs | mission show/state/next | Wave 1 evidence |
| R008 | dependency-ordered roadmap | wave regression | roadmap | current next action | roadmap evidence |
| R009 | authority adapter/aggregate | Wave 2 tests | authority/provider docs | aggregate surface | Wave 2 evidence |
| R010 | recovery/checkpoint contract | Wave 3 tests | recovery docs | recovery/checkpoint surfaces | Wave 3 evidence |
| R011 | live command routing | live discovery tests | CLI docs | all mission-native surfaces | live discovery evidence |
| R012 | durable runtime adoption | temp-independence/replay tests | runtime ownership docs | mission remains discoverable | durable runtime evidence |
| R013 | superseded by later activation boundary | no provider/execution checks | current boundary docs | next action remains pre-provider | ledger/audit |
| R014 | P3 scoped resolver | P3 cardinality suite | P3 contract docs | admitted state | P3 corrective |
| R015 | one-action transition discipline | admission/bootstrap replay | lifecycle procedure | native next | activation evidence |
| R016 | P4 scoped resolver | P4 cardinality suite | P4 contract docs | bootstrap/provider boundary | P4 corrective |
| R017 | regression classification | admission/bootstrap suites | runtime location docs | candidate state | regression evidence |
| R018 | provenance/current-baseline model | lineage tests | baseline model | postpublication reconciliation field | `BASELINE-PROVENANCE-MODEL.md` |
| R019 | `resolve_provenance_lineage` and reconciliation verifier | descendant/non-descendant/forgery tests | fail-closed lineage docs | mission state recovered | `TEST-RESULTS.md` |
| R020 | durable reconciliation receipt | first/replay | receipt ownership docs | native surfaces after reconcile | `ZEUS-NATIVE-VERIFICATION.md` |
| R021 | canonical postpublication state | eight mission-native commands | lifecycle state docs | state/readiness/eligibility/next | native verification |
| R022 | live status projection/reconciliation | status contract suite | status contract docs | status JSON agrees with mission state | status report |
| R023 | validation matrix | required validation commands | validator profiles | platform/Operation Beta surfaces | `VALIDATION-REPORT.md` |
| R024 | explicit no-progression boundary | process/native/git/EOS checks | lifecycle boundary docs | provider fields absent/not evaluated | completion report |
| R025 | projection priority rule | projection-vs-fallback tests | architecture/procedure rule | native live state | controlled reconciliation |
| R026 | hardcoding audit | static search and fallback conflict tests | fallback documentation | live IDs/baselines in output | `HARDCODING-AUDIT.md` |
| R027 | live operand resolution | payload and source projection checks | receipt generation procedure | mission/WOP/baseline fields | provenance model |
| R028 | reproducible digest/lineage | recomputation/replay | receipt schema/docs | identical native state on replay | test results |
| R029 | current controlled rule | semantic/document validation | architecture + operational runtime docs | status/verification surfaces | controlled reconciliation |
| R030 | session ledger and omission audit | ledger consistency checks | evidence procedure | final native state | final audit |
| R031 | bounded current corrective | scope checks | current boundary docs | no provider/execution | completion report |

