# Mission G.1 Qualification Evidence Plan

Date: 2026-07-25
Status: Complete

Mission G.1 re-executes the existing four-case qualification matrix without
changing implementation. Fixed timestamps within the fixture lease make every
input reproducible. The committed ADRs, checksum manifest, reconciliation
report and disagreement approval record form one bounded evidence package.

Future Mission H qualification shall:

1. require exactly the four ADRs in the authoritative evidence directory;
2. verify `SHA256SUMS`;
3. regenerate and byte-compare all four records;
4. confirm two agreements and the two accepted disagreement classes;
5. stop if any additional, missing, changed or unclassified record exists.

No runtime directory is authoritative for this qualification boundary.
