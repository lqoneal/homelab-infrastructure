# Live Transaction Reconciliation

Before corrective, the former selector exposed two current tips:

- `PUBLICATION-9e51dd4c-15d2-540b-aad5-6ad8c4a92bda` — `PUBLICATION_QUALIFIED`
- `PUBLICATION-bd7546d2-377f-569a-9530-f07999ba12b2` — `CANDIDATE_ISOLATED`

Both named `PUBLICATION-35b59c05-31bb-5d45-a7fc-4934c33b6496` as predecessor.
The reconciled derived dispositions are:

- `PUBLICATION-bd7546d2-377f-569a-9530-f07999ba12b2`: `CURRENT`
- `PUBLICATION-35b59c05-31bb-5d45-a7fc-4934c33b6496`: `SUPERSEDED`
- `PUBLICATION-9e51dd4c-15d2-540b-aad5-6ad8c4a92bda`: `HISTORICAL_QUALIFIED`

Mission status now returns PASS, the requested current publication, cohort
`COHORT-fbc7287e-b18f-5bab-a1aa-fa996fd82d64`, and
`VERIFY_PREPUBLICATION`. Direct lookup of `35b59…` remains readable and reports
`current_publication=false`. No live transaction or receipt was edited.
