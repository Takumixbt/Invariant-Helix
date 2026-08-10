# Nemesis skill bridge

Binds nemesis-auditor (0xiehnnkta, MIT) to the `first-principles` and `invariant-state`
lenses via the nemesis loop (`references/lenses/nemesis-loop.md`). Multi-language
(Solidity, Move, Rust, Cairo, Go, TypeScript).

## Install (optional)

```bash
git clone https://github.com/0xiehnnkta/nemesis-auditor.git
cp -r nemesis-auditor/.claude /path/to/your-project/
# then: /nemesis  (full), /nemesis --pass1 (Feynman), /nemesis --pass2 (State)
```

## Bridge

- `.audit/findings/feynman-pass[N].md` / `state-pass[N].md` → `hypothesis` findings on
  the matching lens, with the alternating-pass provenance kept as evidence.
- `nemesis-verified.md` → ingested as findings **at hypothesis status**; the upstream
  "verified" label is advisory. IH re-runs G8 falsification with an independent
  verifier before any release.

## Rule

Apply the anti-confirmation rules: the next branch receives evidence and questions, not
the prior verdict; shared-premise agreement does not reach high confidence
(`converge_findings` enforces this). When the skill is absent, IH runs the loop natively
from the two lens profiles.
