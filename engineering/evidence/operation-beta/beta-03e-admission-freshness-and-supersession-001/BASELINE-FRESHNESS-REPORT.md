# Baseline Freshness Report

The historical admission was bound to
`bf47128d100a22cd08be9f112c45b04125b6945b`. Current canonical `HEAD` is
`b349b1b77d1008b4fb88b908f2ee8fa6899dfd71`. The old admission is therefore
stale for new execution. The execution boundary rejects it before creating an
execution record.

Fresh admissions bind the observed current `HEAD` and fail closed when it
changes.
