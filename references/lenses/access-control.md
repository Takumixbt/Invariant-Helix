# Lens: access control

**Role.** You obtain or exercise authority outside its intended scope.
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Enumerate authority.** List every privileged action and the exact guard that
  gates it. A function with no modifier but an internal `msg.sender`/signer check is
  role-gated, not permissionless — verify the body.
- **Missing/weak guards.** Permissionless functions that write privileged state;
  initializers reachable twice; `initializer`/`reinitializer` gaps; unprotected
  `upgradeTo`, `setOwner`, `setTreasury`, `setStrategy`.
- **Confused deputy.** A trusted contract forwards an attacker-chosen call; router or
  multicall executing with the victim's authority; `delegatecall` into attacker code.
- **Role transfer vs action delay.** A timelock on role *transfer* does not protect
  instant operational functions a compromised holder can still call.
- **Two-step ownership gaps.** `acceptOwnership`/`acceptMsig` with a `msg.sender ==
  pending` check but no zero-address guard.
- **Signature-as-auth.** Authorization by signature without domain separation, nonce,
  deadline, or replay protection (overlaps trust-gap).

## Chain-neutral core

Every authority edge in the graph must have a proof: who may traverse it, and what
guard enforces that. Find edges with no guard, or a guard weaker than the authority
it protects.

## Per-family notes

- **evm** — modifiers vs internal checks; `tx.origin`; proxy admin vs implementation
  admin confusion.
- **solana** — `is_signer`, PDA seed ownership, `has_one`, account substitution: an
  attacker passes a look-alike account the program never checks owner/authority on.
- **move** — capability resources (`key`/`store` abilities); a capability moved or
  copied out of scope; `signer` vs address arguments.
- **cosmwasm** — `info.sender` checks, admin migrate authority, reply-handler
  impersonation.
- **cairo/starknet** — `get_caller_address`, account-abstraction validation, L1↔L2
  message senders.
- **cardano-utxo** — required signatories in script context; minting policy authority.

## Proof fields

`proof: the actor, the guard bypassed, and the privileged state reached`.
