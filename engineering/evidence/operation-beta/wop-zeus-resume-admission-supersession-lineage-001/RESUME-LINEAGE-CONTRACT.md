# Resume Lineage Contract

Resume resolves the Stage 1 receipt admission, follows exactly one validated
`superseded_by` link to a terminal successor, and accepts either identity only
when it belongs to that chain. Every link must bind the same transaction,
package digest, source digest, authority snapshot, repository, and current
published baseline. Resolution is read-only and returns the terminal successor.

Published Operational Alpha authority remains the governing authority chain;
this corrective consumes the submission authority and creates no authority
decision.
