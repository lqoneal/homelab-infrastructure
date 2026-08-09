# Cohort Authority Model

The cohort is bound to live Mission ID, WOP ID, repository identity, qualified
source IDs, source context digests, and live repository provenance. A shared
path is authorized when every current source claim belongs to the same active
cohort. A claim outside the cohort, stale source qualification, wrong identity,
or missing dependency fails closed.

The cohort contains no final Git path list. Candidate paths and traceability
are derived from the cohort member manifests at resolution time.
