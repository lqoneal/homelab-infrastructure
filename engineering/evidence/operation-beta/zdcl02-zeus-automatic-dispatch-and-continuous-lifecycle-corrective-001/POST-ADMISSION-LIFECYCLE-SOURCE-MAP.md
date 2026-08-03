# Post-Admission Lifecycle Source Map

`Stage1Runtime._resume_development` owns the Development continuation;
`development_dispatch.py` owns provider-neutral registry selection; the
existing receipt-backed `Stage1Store` owns persistence and replay.
