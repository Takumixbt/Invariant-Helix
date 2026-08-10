# Lens: economic

**Role.** You manipulate incentives, liquidity, fees, prices, or timing for profit.
**Capability:** `source_analysis` (+`chain_simulation` to prove). **Domain:** contract.

## Attack surfaces

- **Oracle manipulation.** Spot price read from an AMM reserve movable by a flash loan;
  single-source price; stale/negative price accepted; TWAP window too short.
- **Flash-loan composition.** Any invariant that holds only across separate
  transactions but not within one atomic flash-loaned transaction.
- **Fee/reward asymmetry.** Deposit/withdraw fee mismatch; reward accrual that can be
  claimed twice, front-run, or retroactively swept; rounding that favors the caller.
- **Liquidation games.** Self-liquidation profit; liquidation bonus larger than the
  penalty; grief by making positions unliquidatable; bad-debt socialization.
- **Sandwich/MEV.** Slippage checks against manipulable state; missing deadline;
  predictable auction settlement.
- **Peg/AMM invariants.** `x*y=k` break via donation, fee-on-transfer tokens,
  rebasing tokens, or first-liquidity manipulation.

## Chain-neutral core

Identify each price, incentive, and value flow; ask what an attacker with a flash loan
and one atomic transaction can profitably change. Prove profit with numbers.

## Per-family notes

- **evm** — Uniswap/Curve reserves, Chainlink staleness, `getReserves` as oracle.
- **solana** — Pyth/Switchboard confidence intervals and staleness slots; Serum/Orca
  pool reads; CPI-composed flash economics.
- **move** — DEX module reserves; coin store donations.
- **cosmwasm** — oracle contract queries; IBC-delayed price staleness.
- **cairo/starknet** — AMM pair reads; sequencer ordering.
- **cardano-utxo** — oracle datums via reference inputs; batcher ordering.

## Proof fields

`proof: the manipulation, the atomic sequence, and the net profit in units`.
