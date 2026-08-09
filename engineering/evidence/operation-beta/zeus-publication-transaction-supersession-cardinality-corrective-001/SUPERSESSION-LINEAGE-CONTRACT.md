# Supersession Lineage Contract

A successor records `supersedes_publication_id`; the predecessor is never
rewritten. The successor's immutable milestone receipts repeat and digest-bind
that edge. Canonical resolution validates the successor and every authoritative
lineage node before using the edge.

The target must exist exactly once and share repository, Mission, and WOP with
the successor. Self-links, cycles, missing targets, duplicate identities,
cross-scope targets, and multiple nonterminal successors of one target fail
closed. A terminal-qualified historical sibling cannot compete with one open
recovery/reprepare successor; two open siblings remain incompatible.

Direct Publication-ID lookup preserves historical audit access. Mission lookup
uses the derived disposition and excludes superseded/historical records from
current cardinality.
