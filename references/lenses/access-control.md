# Lens: access control

**Role.** Obtain or exercise authority outside its intended scope.  
**Capability:** `source_analysis`. **Domain:** contract.

## Concrete moves (run these)

1. **Permissionless privileged write** — list every `external`/`public` non-view function that writes non-`msg.sender`-scoped state without a modifier or `msg.sender` check.
2. **Initializer re-entry** — call `initialize` / `__init` twice after deploy; proxy vs implementation admin confusion.
3. **Role transfer ≠ action delay** — if only ownership transfer is timelocked, exercise instant `setTreasury` / `setFee` / `pause` as compromised admin.
4. **Two-step ownership half-done** — set `pendingOwner` to attacker; see if anything privileged is callable before `acceptOwnership`.
5. **Signature auth** — replay, cross-contract, missing domain separator, zero deadline, malleable sig.
6. **Confused deputy** — router/multicall/forwarder executes attacker calldata with protocol authority.
7. **tx.origin** — any auth on `tx.origin` → phishing path.
8. **Default admin** — `DEFAULT_ADMIN_ROLE` / `owner()` can drain or upgrade; document blast radius.

## Attack surfaces

- Missing/weak guards on privileged state
- Initializers without `initializer` / reinitializer
- `upgradeTo`, `setOwner`, `setStrategy`, emergency withdraw
- `delegatecall` into attacker code; proxy admin vs implementation
- Capability/resource movement (Move), PDA substitution (Solana)

## Proof fields

`proof: actor, guard bypassed, privileged state reached, concrete call sequence with values`

## Required adversarial pass

- Build an authority matrix: actor → entry point → object/amount/domain → state or asset
  reached. Check the same action through direct, batch, router, callback, meta-transaction,
  initializer, migration, and emergency paths.
- For signatures, bind signer, chain/domain, contract, nonce, deadline, operation, object,
  and amount. Test replay after success, expiry, revocation, and a different target.
- Treat proxy admin, implementation, timelock, guardian, and default-admin roles as
  separate principals. A delayed ownership transfer does not delay every privileged setter.
- Negative control: the intended caller succeeds on the intended object while a second
  identity, stale signature, wrong domain, and wrong object each fail without mutation.
