# Runtime Persistence Report

Launch journal persistence uses a transaction-scoped lock, temporary file, fsync, and atomic replace. Session materialization is verified before the launch reaches `EXECUTING`; failed materialization invokes cleanup and records `ROLLBACK_REQUIRED`.
