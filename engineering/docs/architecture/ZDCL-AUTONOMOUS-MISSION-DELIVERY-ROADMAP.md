# ZDCL Autonomous Mission Delivery Roadmap

The canonical sequence is: direct Development WOP submission → autonomous implementation and correction → admission and execution → qualification → publication approval when required → publication → EOS synchronization → canonical Mission Contract activation → discovery → operational execution → qualification and closeout. Publication is an output gate, not a submission prerequisite.

Canonical mission publication is a lifecycle phase, not a separate operator-managed repair workflow. Each phase consumes the prior receipt-backed identity and produces a durable, verifiable derived projection.

Dispatch follow-through is also autonomous: `DISPATCHED` enters a bounded provider-launch transaction, then session verification and `EXECUTING`. Provider adapters are qualified dependencies, not authority sources. Missing or failed adapters produce durable blockers; retry and failover never broaden the WOP effect profile.

ZDCL-02 provider control is machine-mediated. The canonical operator action is
`zeus submit <authorized-wop>`. Zeus constructs the versioned Codex context
envelope, invokes the low-level `engctl codex` service, supervises its process
group, and reconciles provider/session receipts. Direct `engctl codex` is
compatibility infrastructure only and is not a governed mission entry point.
