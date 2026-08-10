# Pashov integration

Pashov's skills provide the specialist depth for the contract and protocol
branch. Invariant Helix keeps the taxonomy but places it inside a larger
evidence and graph system.

## Pre-audit x-ray

Before specialist review, extract:

- project purpose and intended users;
- architecture, trust boundaries and custody points;
- all entry points and wrappers;
- state variables and derived values;
- authority, upgrade and emergency controls;
- external calls, oracles, bridges and callbacks;
- event and off-chain accounting dependencies;
- test coverage, deployment assumptions and code history;
- changed code and code that is inherited but security-critical.

Output an architecture brief, entry-point table, value-flow map and initial
invariant list. The x-ray is a model-building phase, not a security verdict.

## Specialist matrix

Run the following lenses against the chain-neutral model:

| Lens | Primary question |
|---|---|
| Access control | Can an actor obtain or exercise authority outside its intended scope? |
| Math and precision | Do units, rounding, bounds and conversion order preserve value? |
| Economic | Can incentives, liquidity, fees, prices or timing be manipulated profitably? |
| Execution trace | What exact calls, state writes, callbacks and failure paths occur? |
| Invariant/state | Do all mutation paths preserve required relationships? |
| Periphery/integration | Do wrappers, routers, adapters and peripheral contracts preserve safety? |
| First principles | Why does each guard, order and assumption exist? |
| Asymmetry | Do parallel or inverse operations behave consistently? |
| Boundary | What happens at zero, one, maximum, empty, stale and repeated states? |
| Numerical gap | Are cached, scaled, truncated or time-dependent values misaligned? |
| Trust gap | Is an external actor, oracle, relayer or admin trusted beyond its proof? |
| Flow gap | Can value or authority cross a path without its required control? |

The names are roles, not required model personalities. A generic harness may
run them as processes, shell jobs or sequential prompts.

## Four validation gates

Every material hypothesis must pass:

1. execution: the claimed operation is actually performed;
2. reachability: an allowed actor can reach it from a valid initial state;
3. trigger: the exact conditions and sequence are reproducible;
4. impact: the consequence is real, scoped and correctly rated.

Add the Invariant Helix falsification gate after these four. An auditor finding
that passes its own trace but fails independent falsification is not released.

## Tooling and tests

Use the project's native tools where possible:

- Foundry or equivalent for EVM unit, fork and invariant tests;
- Medusa or Echidna for stateful/property fuzzing;
- chain-native test frameworks for Solana, Move, CosmWasm, Cairo and others;
- graph queries to select handlers, actors, boundaries and state transitions;
- runtime traces and state diffs to connect code claims to behavior.

Do not treat a tool's green result as proof of safety. Test properties must
cover the right actors, sequences, units and failure paths.

## Integration with Nemesis

Nemesis Feynman occupies the first-principles role. Nemesis State occupies the
invariant/state role. They exchange:

- exposed assumptions;
- state variables and derived values;
- ordering concerns;
- masking code;
- parallel paths;
- multi-transaction sequences;
- verifier questions.

The other ten specialists remain independent. This prevents the feedback loop
from becoming an echo chamber around only two bug classes.

## Corrected uncertainty rule

Uncertain semantics are not permission to proceed as safe. Use:

~~~text
UNKNOWN → needs evidence
PLAUSIBLE → hypothesis
REACHABLE → execution gate passed
REPRODUCED → proof gate passed
VERIFIED → positive proof + falsification attempt + independent adjudication passed
~~~
