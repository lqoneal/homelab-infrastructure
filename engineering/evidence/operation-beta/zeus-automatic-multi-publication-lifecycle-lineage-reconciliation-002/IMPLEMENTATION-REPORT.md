# Implementation Report

Changed runtime behavior:

* added generic `resolve_commit_lineage()` for arbitrary recorded commit pairs;
* retained `resolve_provenance_lineage()` as the live HEAD/origin parity wrapper;
* changed reconciliation verification to validate each receipt at its recorded
  baseline and then prove that baseline is an ancestor of the live baseline;
* changed current reconciliation resolution to use live Git/EOS projections,
  allowing zero receipts, one current supplemental receipt, or historical
  receipts beneath the live projection;
* retained fail-closed duplicate-current, digest, identity, repository, EOS,
  and ancestry checks;
* removed the resolver's requirement that a reconciliation directory or a new
  receipt exist for every descendant publication;
* preserved the P2/P3/P4 receipts and the prior reconciliation receipt bytes.

No hardcoded current publication baseline was added. No lifecycle transition,
provider operation, execution session, mission work, publication, push, or EOS
synchronization was performed.
