# Lens: share and exchange rate

**Role.** You attack the claim-to-value relationship: what a share entitles its holder to,
and whether redemption honours it. **Capability:** `source_analysis`. **Domain:** contract.

Vaults, LP tokens, receipt tokens, staking positions, and rebasing wrappers all reduce to
one question: *does `shares -> assets` round-trip without leaking value to the caller?*

## Attack surfaces

- **First-depositor / inflation.** Mint 1 wei of shares, donate assets directly to the
  vault, then let the next depositor round to zero shares. Check whether the vault seeds
  dead shares, uses virtual offsets, or reads `balanceOf(this)` as the denominator.
- **Donation skew.** Any exchange rate whose denominator is `token.balanceOf(address(this))`
  can be moved by an unsolicited transfer. Trace whether internal accounting or raw
  balance is authoritative — mixing the two is the bug.
- **Round-trip asymmetry.** `deposit(x) -> withdraw(all)` must never return more than `x`.
  Deposit rounds shares **down**, withdraw rounds assets **down**, debt rounds **up**.
  Any pair rounding in the caller's favour is extractable; compoundable = critical.
- **Rate read at the wrong moment.** A rate snapshotted before a mint/burn in the same
  function differs from the post-state rate. Check ordering against every `totalSupply`
  and `totalAssets` mutation.
- **Preview vs actual divergence.** `previewDeposit`/`previewRedeem` that disagree with the
  executing path let an integrator commit to a price that will not be honoured.
- **Loss socialization.** When the vault takes a loss, who absorbs it? Look for a path
  where an exiting holder redeems at the pre-loss rate and leaves the loss to the rest.
- **Fee-on-transfer / rebasing underlying.** Assets received `!=` assets requested; if the
  vault credits the requested amount, it mints unbacked shares.

## Chain-neutral core

Identify the *claim* (share, receipt, position) and the *backing* (assets, collateral,
reserve). Write the intended relation as an equation, then find any reachable path where
the equation does not hold after the call.

## Per-family notes

- **evm** — ERC-4626 `totalAssets`/`convertTo*`; virtual shares/offset; `balanceOf(this)`.
- **solana** — pool token supply vs vault token account balance; donation to the ATA.
- **move** — coin supply vs resource-held reserve; `Supply<T>` accounting.
- **cosmwasm** — cw20 supply vs bank balance held by the contract.

## Proof fields

`proof: the round-trip with concrete amounts showing value gained or lost`.
