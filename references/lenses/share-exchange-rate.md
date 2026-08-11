# Lens: share / exchange rate

**Role.** Attack vault/share math: inflation, donation skew, preview vs actual.  
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

1. **First depositor inflation** — `totalSupply == 0` mint; donate assets; next depositor rounds to 0 shares.
2. **Virtual offset** — check dead shares / virtual assets; if absent, prove inflation.
3. **Round-trip** — deposit X, withdraw all; compare assets out vs in.
4. **preview vs actual** — `previewDeposit` / `previewRedeem` disagree with execute under fee-on-transfer.
5. **Donation skew** — direct transfer of underlying; inflate price; redeem advantage.
6. **Loss socialization** — who eats bad debt or negative yield; front-run the snapshot.

## Proof fields

`proof: shares minted/burned, assets moved, exchange rate before/after, victim loss`

## Required adversarial pass

- Test the empty, first-depositor, donation, virtual-offset/dead-share, loss, fee,
  rebasing, and fee-on-transfer states. Compare preview and execute with exact integers.
- Run deposit → donate → deposit → redeem and its inverse with both asset directions.
  Track raw assets, accounted assets, total shares, rounding direction, and each holder's
  claim; a one-unit victim loss can compound into a material drain.
