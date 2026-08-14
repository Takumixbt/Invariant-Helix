# Install — Invariant Helix

Helix is a **skill**, not an app. Its core is markdown and judgment; it needs no
runtime. Everything below except Tier 0 is optional — each tier adds a
capability, and any capability you skip degrades to coverage-debt, never to a
silent gap.

---

## Tier 0 — Core (required; this is all you truly need)

Drop the skill where your harness loads skills.

### Claude Code

```bash
git clone https://github.com/Takumixbt/Invariant-Helix.git ~/.claude/skills/invariant-helix
# start a fresh session — skills load at startup
```

Or per-project: clone into `<project>/.claude/skills/invariant-helix/`.

Invoke with `/helix <link>`, `/feynman`, or `/state-audit`.

### DeepSeek / Hermes harness

Place the repo where your Hermes agent runtime reads skills/instructions (the
same location it loads other skill markdown from), or point the runtime at
`SKILL.md` as the entry instruction. The skill is plain markdown + JSONL — any
harness that can read files and call tools runs it.

That's the whole core install. You can audit right now.

### Any other agent runtime

See **`AGENTS.md`** for the full agent-readiness contract — how to boot Helix in a
generic agent loop, the host-capability contract (what the host must provide and
how Helix degrades when it doesn't), and a smoke test to confirm it loaded.

---

## Tier 0.5 — Running Helix on DeepSeek via the Claude CLI (optional bridge)

If you want to drive Claude Code's harness but with DeepSeek behind it (single
key, `deepseek-v4-flash`/`-pro`), export these before starting the CLI:

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max
export ANTHROPIC_AUTH_TOKEN="your-deepseek-token"
```

Windows PowerShell: the same names as `$env:NAME = "..."`.

> **Honest note on model tiers.** Helix does **not** rely on a big model
> verifying a small model's work. On a single key every role is the same model,
> and that's fine — rigor comes from the **alternating loop** (two different
> interrogations of the same code) and **independent falsification at the gate**,
> not from model ranking. The `SUBAGENT_MODEL`/`OPUS`/`HAIKU` names above are
> provenance labels for the harness, not a real tier hierarchy on a single key.
> Helix is designed for exactly this reality.

---

## Tier 1 — Web tools (optional; Strand A acceleration)

```bash
# an adaptive, JS-rendering crawler for the http_crawl capability
#   (any headless-browser crawler that exports routes/forms/XHR works)

# recon CLIs — via apt/brew/go install, whatever your platform uses
#   amass subfinder httpx ffuf gobuster wfuzz nmap nuclei sqlmap trufflehog gitleaks
```

A Chromium is needed for JS-rendered crawling; on a managed harness one may
already be present (Playwright-configured).

Absent → recon falls back to `curl` + JS parsing, and the missing pieces become
coverage-debt.

---

## Tier 2 — Burp proxy (optional; you said you have it)

Helix drives Burp through a **Burp MCP bridge** — an MCP server loaded as a Burp
extension. Prefer an agent-oriented build (newest-first proxy history, readable
site map, a full Repeater send+read loop) over the stock extension, which serves
oldest-first history and truncates responses.

Load the bridge's jar in Burp: **Extensions → Add → Java →** select it. Then
point your MCP client (the desktop/CLI harness, or the Hermes MCP config) at the
bridge's local address (commonly `http://127.0.0.1:9876`).

**Read before using on someone else's target:** some agent-oriented builds ship
with approval prompts **OFF** — a connected client can send requests and read
history without asking. Re-enable the prompts for third-party engagements. Keep
the bridge bound to `127.0.0.1`. Full safety notes: `references/local-tooling.md`.

Absent → `proxy_observation`/`request_replay` fall back to scripted `curl`;
`active_scan`/`oob_observation` become coverage-debt.

---

## Tier 3 — Web3 tools (optional; Strand B verification)

```bash
# Foundry — the poc_evm capability (turns REACHABLE findings into CONFIRMED)
curl -L https://foundry.paradigm.xyz | bash && foundryup    # forge cast anvil

# optional deeper coverage
#   slither  (static, context-filtered)   pip install slither-analyzer
#   echidna / medusa  (property fuzzing)  — per their install docs
#   halmos  (symbolic)                    — per its docs
```

For non-EVM: `cargo`/`anchor` (Solana), `aptos`/`sui` (Move), `scarb` (Cairo) —
install the chain's toolchain as the target requires.

Absent → findings can still reach REACHABLE by code trace, but a
severity-critical finding without a runnable PoC stays a strong lead, not a
CONFIRMED critical (`references/judging.md`).

---

## Tier 4 — WSL routing (Windows operators)

If you're on Windows and your tools live in WSL, install a distro
(`wsl --install`) and put the Tier 1/3 tools inside it. Helix auto-routes:
native-first, WSL-fallback, path-translated. Nothing to configure — the routing
rule and path handling are in `references/local-tooling.md`. Recommended: run the
whole Linux toolchain in WSL for consistency, and let PowerShell handle only what
genuinely runs there.

---

## Verify your install

```
/helix --check         # prints the tool roster: what's present, what's debt
```

(Or just drop a scope link — intake writes `.audit/tooling.md` with the
available-vs-absent map on the first run, and every coverage gap lands in the
report's Coverage section.)

Nothing here is a prerequisite for hunting except Tier 0. Everything else makes
Helix faster and its proofs stronger — it never makes the audit possible or
impossible.
