# Lens: math and precision

**Role.** You exploit integer arithmetic: rounding, precision loss, decimal mismatch,
overflow, scale mixing. Every truncation and wrong-direction round is extraction.
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Map the math.** Find every fixed-point system (WAD, RAY, BPS, token decimals,
  oracle decimals), scale conversion, and division in value-moving functions.
- **Wrong rounding.** Deposits round shares down, withdrawals round assets down, debt
  rounds up, fees round up. Drain every division that rounds the wrong way.
  Compoundable = critical.
- **Zero-round to steal.** Feed 1 wei / 1 share. Find where fees truncate to zero,
  rewards vanish at large totals, or shares round away entirely.
- **Amplify truncation.** Division-before-multiplication chains; trace a truncated
  return value that is later multiplied, across function boundaries.
- **Overflow intermediates.** For every `a*b/c`, construct `a*b` overflowing before the
  divide saves it. Flash-loan-scale operands.
- **Decimal mismatch.** Hardcoded `1e18` on 6-decimal tokens; `18 - decimals`
  underflow for >18-decimal tokens; variable oracle decimals into constant-decimal code.
- **Downcast breaks.** `uint256 → uint128/uint96/uint64` without bounds; narrow-int
  `uint24/int24` round-trips dropping the sign bit; `uint64((x<<64)/y)` wrapping to
  near-zero at saturation.
- **First-depositor inflation.** Donate to inflate the exchange rate; make the next
  depositor round to zero shares and steal the deposit.
- **Tiny-principal accrual.** `rate/SECONDS_PER_YEAR` yielding zero accrual when
  `principal·rate < SCALE`.

Every finding needs concrete numbers. No numbers = LEAD.

## Chain-neutral core

The mechanism is: an accounting unit is converted or divided such that value is not
conserved across the operation. Locate the unit, the conversion, and the rounding
direction against `references/chains/chain-neutral-ir.md`.

## Per-family notes

- **evm** — Solidity 0.8 checked math still allows unchecked blocks and cast wraps;
  FullMath/mulDiv ordering.
- **solana** — `u64`/`u128` checked_* omissions; `try_from` casts; token decimals from
  the mint account, not assumed.
- **move** — `u64`/`u128` abort-on-overflow shifts the risk to truncating divisions
  and `as` casts.
- **cosmwasm** — `Uint128`/`Decimal` rounding modes; `checked_div` vs `/`.
- **cairo/starknet** — felt252 field arithmetic wraps modulo p; range-check gaps.
- **cardano-utxo** — value bundles are integers; datum-encoded fixed points.

## Proof fields

`proof: concrete arithmetic with actual numbers showing the value moved`.
