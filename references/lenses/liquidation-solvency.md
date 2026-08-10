# Lens: liquidation and solvency

**Role.** You break health calculations, liquidation incentives, and bad-debt handling.
**Capability:** `source_analysis` (+`chain_simulation` to prove). **Domain:** contract.

## Attack surfaces

- **Health factor manipulation.** Every input to the health formula — price, index,
  collateral factor, debt accrual — is an attack surface. Move any one within a single
  transaction and check whether a healthy position becomes liquidatable, or vice versa.
- **Self-liquidation profit.** Liquidate your own position and net a gain from the bonus.
  Compute the bonus against the penalty; if `bonus > penalty`, it is free money.
- **Unliquidatable positions (griefing).** Find a state where liquidation reverts — dust
  balances below a minimum, a paused token, a full-repay requirement the liquidator cannot
  meet, an unbounded loop over the position's collateral list. An unliquidatable underwater
  position becomes protocol bad debt.
- **Partial-liquidation loop.** Repeated partial liquidations that each round in the
  liquidator's favour, or that leave the position *less* healthy than before.
- **Bad-debt socialization.** When collateral < debt, who absorbs it? Look for a path where
  the loss is deferred and an informed actor exits at full value first — a bank run.
- **Liquidation during pause / oracle downtime.** Positions frozen while prices move, then
  mass-liquidated on resume. Check the sequencer-uptime and staleness guards.
- **Wrong close factor.** A close factor of 100% on a marginally unhealthy position
  over-punishes; a close factor too small leaves the position underwater after liquidation.
- **Collateral seize ordering.** When several collaterals back one debt, the seize order
  determines who eats the illiquid asset.

## Chain-neutral core

State the solvency invariant explicitly — `Σ collateral_value >= Σ debt_value` at all
times — then find a reachable sequence that violates it, or a state where restoring it is
impossible.

## Per-family notes

- **evm** — Aave/Compound health factor, close factor, liquidation bonus, `accrueInterest`
  ordering.
- **solana** — obligation accounts refreshed per instruction; stale refresh windows.
- **cosmwasm** — liquidation submessage failure leaving partial state.

## Proof fields

`proof: the position, the manipulated input, and the resulting solvency violation in units`.
