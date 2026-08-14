# Property Fuzzing — proving invariants, not just reading them

Reading an invariant tells you it *should* hold. Fuzzing tells you whether it
*does*. This is the deepest rigor Helix has for web3: state an invariant as an
executable property and throw thousands of randomized sequences at it. If the
fuzzer finds a counterexample, you have a bug with a concrete reproduction — the
strongest evidence there is.

**When to use it:** on any protocol where the `invariant-agent` has stated
invariants that a code trace can't fully settle — accounting conservation, share-
price monotonicity, solvency, access-control totality. Fuzzing turns a REACHABLE
invariant finding into a CONFIRMED one, and finds invariant breaks no human trace
would reach. It's a capability (`property_fuzzing`); absent a fuzzer, it degrades
to coverage-debt and the invariant stays a strong lead.

---

## The tools (capability `property_fuzzing`)

| Tool | Use | Style |
|---|---|---|
| **Foundry invariant tests** | EVM, first choice — already present if Foundry is | `invariant_*` + handler-based stateful fuzzing |
| **Echidna** | EVM, property + assertion + optimization modes | Haskell-backed, deep |
| **Medusa** | EVM, parallelized coverage-guided | Go, fast, coverage-guided |
| **Halmos** | EVM, symbolic (proves, not just samples) | bounded symbolic execution |
| chain-native | Move Prover (Aptos/Sui), `cargo fuzz`/kani (Rust/Solana) | per-chain |

Foundry invariant testing is the default because it's already installed wherever
`poc_evm` is, needs no extra dependency, and its handler pattern models the
adversarial multi-tx sequences Helix's Feynman Q7 already reasons about.

---

## The workflow

```
1. TAKE the invariant from x-ray / invariant-agent, stated as a property:
     "sum of all user balances == totalSupply"
     "vault share price never decreases except on a realized loss"
     "no function lets debt exceed collateral * maxLTV"
2. ENCODE it as an executable assertion in the target's framework.
3. WRITE a handler exposing the protocol's state-changing functions to the fuzzer
   (deposit, withdraw, borrow, liquidate, transfer…) with bounded random inputs.
4. RUN with a high run count; let the fuzzer explore sequences.
5. If it BREAKS the invariant → the shrunk counterexample IS the PoC. Confirmed.
   If it HOLDS after deep fuzzing → the invariant is strong evidence the property
   holds (not a proof unless symbolic; note the run count and coverage).
```

### Foundry invariant skeleton

```solidity
// test/audit/Invariant.t.sol
contract InvariantTest is Test {
    Protocol p;
    Handler h;                          // wraps p, bounds inputs, tracks ghost vars

    function setUp() public {
        p = new Protocol();
        h = new Handler(p);
        targetContract(address(h));     // fuzz through the handler
    }

    // the invariant the invariant-agent stated, as code:
    function invariant_solvency() public {
        assertGe(p.totalAssets(), p.totalLiabilities());
    }
    function invariant_sharePriceMonotonic() public {
        assertGe(h.currentSharePrice(), h.lastSharePrice());
    }
}
```

The **handler** is where the rigor lives: it exposes exactly the adversarial
surface (partial ops, extreme values, cross-function sequences from Feynman Q7.8)
and tracks ghost variables the invariant needs. A weak handler fuzzes nothing; a
good handler is the difference between "no counterexample found" meaning something
and meaning nothing.

---

## How it plugs into the audit

- The **invariant-agent** produces the invariant list and hands the high-value,
  trace-unsettled ones here.
- A **counterexample** → a CONFIRMED finding (`invariant-violation` or the specific
  class), PoC = the shrunk sequence, straight into `verified.md`.
- **No counterexample after deep fuzzing** → record it in the coverage section as
  positive assurance ("solvency invariant held over N runs, M sequences") — that
  itself is valuable in a Notion in-house report, and it downgrades the matching
  raw findings.
- **No fuzzer available** → `property_fuzzing` is coverage-debt; the invariant
  findings stay REACHABLE leads, verified by trace only, and the report says the
  properties were not fuzz-tested.

Fuzzing does not replace the loop or the gate — it's a verification *method*
(alongside code trace and hand-written PoC in the engines' Phase-5 gate). It's the
one that scales to sequences a human can't enumerate, which is exactly where the
deepest invariant breaks hide.
