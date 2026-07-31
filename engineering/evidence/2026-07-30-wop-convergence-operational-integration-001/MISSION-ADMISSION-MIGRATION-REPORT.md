# Mission Admission Migration Report

Operational admission consumes an exact WOP/revision/Authority Record selector
and invokes the convergence resolver with action `admit_mission`. A missing
selector or unresolved record causes `AUTHORITY_FAILURE`; no legacy authority
source is consulted. Qualification admission is unchanged.
