# Interruption Recovery

The activation journal records `PREPARED` or `COMMITTED`. An interrupted
transaction is not active; recovery revalidates publication, EOS, platform,
package, and cardinality before replay or rollback.
