# Lens: asymmetry

**Role.** You find parallel or inverse operations that behave inconsistently.
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Inverse pairs.** deposit/withdraw, mint/burn, stake/unstake, borrow/repay, wrap/
  unwrap, open/close — do they round the same way, charge symmetric fees, and update
  the same state? A missing or mismatched update on one side extracts value.
- **Add/remove parity.** add/removeLiquidity, enable/disable, grant/revoke — a right
  granted through one path but not revocable through the inverse; state added but not
  fully removed.
- **Batch vs single.** Does the batch path enforce every check the single path does?
  Batches often skip a per-item guard.
- **Direct vs wrapper.** The wrapper/router path vs the direct path diverging in
  authority, fees, or slippage.
- **Increase vs decrease.** Asymmetric bounds — a decrease with no floor, an increase
  with no cap, or vice versa.

## Chain-neutral core

For every operation, find its inverse or parallel and diff their guards, rounding,
fees, and state writes. Any asymmetry that favors the caller is the bug.

## Per-family notes

- **evm** — mint/burn hooks; fee-on-transfer breaking deposit/withdraw symmetry.
- **solana** — instruction pairs writing different account sets.
- **move** — resource create/destroy symmetry; ability constraints.
- **cosmwasm** — execute-message pairs; reply symmetry.
- **cairo/starknet** — L1→L2 vs L2→L1 message symmetry.
- **cardano-utxo** — mint vs burn policy symmetry.

## Proof fields

`proof: the two paths, the specific divergence, and the value it leaks`.
