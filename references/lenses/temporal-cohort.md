# Lens: temporal cohort

**Role.** You exploit *when* an actor joined or left relative to a distribution.
**Capability:** `source_analysis`. **Domain:** contract.

Rewards, fees, airdrops, rebases, and slashing all divide value among a set of holders.
The bug is almost never the arithmetic — it is the **membership boundary**: who was
counted, and as of when.

## Attack surfaces

- **Join-just-before / exit-just-after.** Deposit one block before a reward accrues,
  claim, and leave. If accrual is not time-weighted, a one-block holder earns what a
  month-long holder earned. Look for `reward = balance * rate` with no `lastUpdate`.
- **Unclaimed reward theft.** A new depositor's `rewardDebt` must be initialized to the
  current accumulator. If it starts at zero, they claim rewards accrued before they
  existed — a direct drain of prior holders.
- **Exit without settlement.** Withdrawing must checkpoint pending rewards. A path that
  zeroes `balance` before crediting pending value destroys or strands it.
- **Retroactive parameter change.** An admin raising a rate that applies to already-elapsed
  time, or a snapshot taken after a mutation, retroactively re-cuts the pie.
- **Epoch boundary double-count.** Value counted in both the closing and opening epoch, or
  in neither. Test the exact boundary timestamp/block on each side.
- **Slashing/loss applied to the wrong cohort.** A loss incurred at T applied to holders as
  of T+1 lets the responsible cohort exit first.
- **Zero-supply accrual.** Rewards accruing while `totalStaked == 0` are stranded or
  awarded to whoever deposits first. Check the guard.

## Method

Build the cohort timeline explicitly: for each distribution, record who was a member at
accrual, at claim, and at settlement. Then attack every point where those three sets
differ. This is the state the code usually never materializes — which is why the bug
survives review.

## Chain-neutral core

Any `accumulator + per-actor debt` design is a cohort mechanism. Verify the accumulator
advances before membership changes, and that membership changes settle before they mutate
balance.

## Proof fields

`proof: the join/exit timestamps, the accrual window, and the value mis-assigned`.

## Required adversarial pass

- Draw the membership timeline at join, accrual, claim, settlement, exit, epoch rollover,
  parameter update, slashing, and recovery. Compare the three cohorts at each timestamp.
- Test just-before/just-after boundaries, zero-supply accrual, repeated claims, partial
  exit, and a new depositor whose reward debt starts at the wrong accumulator.
