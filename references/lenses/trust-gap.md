# Lens: trust gap

**Role.** You find an external actor, oracle, relayer, or admin trusted beyond its
proof. **Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Oracle trust.** A price/state feed trusted without staleness, deviation, or
  multi-source checks; a manipulable or upgradeable oracle.
- **Relayer/keeper trust.** A relayer whose input is used without validation;
  keeper-provided values (prices, indices, slippage) taken on faith.
- **Bridge/message trust.** A cross-chain message accepted without verifying the source
  chain, sender, nonce, and domain separator; replayable messages; unfinalized state.
- **Admin trust.** A privileged setter that can violate an existing invariant
  (`setReserveCapacity` below current liquidity); instant powers with no timelock that
  can seize or redirect funds.
- **Signature trust.** ECDSA/EdDSA signatures without domain separation, nonce,
  deadline, or `s`-malleability handling; signer set assumed immutable.

## Chain-neutral core

For every value that enters from outside the trust boundary, ask what is proven about
it on-chain. Anything trusted without proof is an attack surface. Distinguish a design
trust assumption (documented, accepted) from an unproven one (a bug).

## Per-family notes

- **evm** — Chainlink staleness, EIP-712 domains, permit replay, `ecrecover(0)`.
- **solana** — Pyth confidence/staleness, signer verification, cross-program trust.
- **move** — capability provenance; oracle module trust.
- **cosmwasm** — IBC packet authenticity, relayer trust, admin migrate power.
- **cairo/starknet** — L1 handler `from_address` checks; account validation.
- **cardano-utxo** — oracle datum authenticity via trusted minting policy or NFT.

## Proof fields

`proof: the trusted input, what is not proven about it, and the resulting exploit`.
