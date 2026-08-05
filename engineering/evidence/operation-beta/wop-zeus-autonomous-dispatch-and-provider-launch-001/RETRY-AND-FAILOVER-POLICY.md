# Retry and Failover Policy

The disposable controller retries recoverable adapter failures at most two times. Failover is not implicit: it requires WOP policy, an unchanged effect profile, and a second qualified provider. No failover was exercised against live state.
