# Stale oracle price accepted during sequencer downtime

Severity: Medium. The lending market reads a Chainlink feed but never checks
`updatedAt` against a staleness threshold, and does not consult the L2 sequencer uptime
feed. During downtime the last price persists; a borrower opens an underwater position
priced at a stale value. Root cause: trust in an external price without a freshness
proof. This is a trust gap, not an oracle manipulation.
