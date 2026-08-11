# Lens: cross-chain state

**Role.** You attack state that is mirrored, bridged, or messaged between chains.
**Capability:** `source_analysis`. **Domain:** contract.

Cross-chain code fails where two ledgers disagree. Messages are asynchronous, reorderable,
replayable, and can fail on arrival — every assumption of atomicity is a bug candidate.

## Attack surfaces

- **State overwrite vs merge.** A message that *sets* remote state (`balance = x`) instead
  of applying a delta (`balance += d`) loses any concurrent local change. Two in-flight
  messages then clobber each other. This is the classic LayerZero/CCIP integration bug.
- **Out-of-order delivery.** Messages are not guaranteed ordered. Replay the same pair in
  reverse and check the final state. Look for a nonce or sequence guard; its absence is
  the finding.
- **Replay across chains/domains.** A message valid on chain A accepted on chain B — check
  the destination chain id, source chain id, and domain separator are all bound *and
  verified*, not merely present.
- **Trusted remote spoofing.** Is the sender verified against a per-chain trusted-remote
  registry, or just non-zero? Can an admin add a remote without a delay?
- **Failed-message handling.** A message that reverts on arrival: is it retryable, stored,
  or silently dropped? A stored failed message that can be force-resumed with attacker
  parameters is a live exploit.
- **Fee/gas griefing.** Under-funded delivery leaving a message permanently stuck, or
  gas-limit assumptions that fail once the destination state grows.
- **Finality assumption.** Acting on source-chain state before finality; a reorg then
  leaves the destination crediting value that no longer exists.
- **Duplicate mint/burn.** Bridged supply must be conserved: `burned_on_A == minted_on_B`.
  Find any path that mints without a corresponding burn, or double-processes a receipt.

## Chain-neutral core

Write the cross-chain invariant as a conservation statement over both ledgers, then attack
the message lifecycle — send, deliver, retry, fail — for a path that breaks it.

## Per-family notes

- **evm** — LayerZero `lzReceive`, CCIP `ccipReceive`, Wormhole VAA verification, canonical
  vs wrapped supply.
- **solana** — Wormhole post/verify VAA, sequence accounts, PDA-derived message accounts.
- **cosmwasm** — IBC packet timeout and acknowledgement handling, `ibc_packet_ack` refunds.
- **cairo/starknet** — L1 handler `from_address` verification, message-consumption ordering.

## Proof fields

`proof: the message sequence across both chains and the resulting state divergence`.

## Required adversarial pass

- Record source chain, destination chain, sender, receiver, nonce, payload hash, asset,
  amount, decimals, finality threshold, and one-time-consumption state as separate facts.
- Test duplicate, reordered, delayed, failed, retried, cross-domain, wrong-sender,
  wrong-asset, and reorged messages. A valid hash without the correct domain is not
  authentication.
- Compare supply and liabilities on both ledgers after every accepted or rejected message;
  failure handling must not mint twice, burn without credit, or strand a refund.
