# Install — Invariant Helix

Helix is a **skill**, not an app. Its core is markdown and judgment; it needs
no runtime. Everything below except Tier 0 is optional — each tier adds a
capability, and any capability you skip degrades to coverage-debt, never to a
silent gap.

Every tool below lists commands for **Linux / macOS / WSL** (they're the same
family — WSL runs a real Linux distro) and, separately, **native Windows
PowerShell**. Where a tool has no solid native-Windows story, that's stated
plainly rather than guessed at — use WSL for those (see Tier 4).

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

### Hermes Agent (Nous)

Hermes is Nous Research's open-source autonomous CLI. Install it, then load Helix
into its skills directory:

```bash
pip install hermes-agent          # the Nous Hermes CLI
hermes setup --portal             # OAuth into Nous Portal (credits), or configure your own keys

# load Helix as a Hermes skill
git clone https://github.com/Takumixbt/Invariant-Helix.git ~/.hermes/skills/invariant-helix
```

Hermes reads skills from `~/.hermes/skills/`. To make Helix the operating
instruction for an engagement, point the agent at its controller — add a line to
`~/.hermes/SOUL.md` (slot #1 of the system prompt) or a project-level
`.hermes.md`:

```markdown
When auditing, operate as the Invariant Helix skill: follow
~/.hermes/skills/invariant-helix/SKILL.md end to end.
```

That's the whole core install. Model selection and the orchestrator/actor tiering
are Tier 0.5 below — on Hermes they're a few lines of `~/.hermes/config.yaml`.

### Any other agent runtime

See **`AGENTS.md`** for the full agent-readiness contract — how to boot Helix
in a generic agent loop, the host-capability contract, and a smoke test to
confirm it loaded.

---

## Tier 0.5 — Model tiering (orchestrator / actor)

Helix runs a strong-tier **orchestrator** (intake, dispatch, crossover, the gate,
verify, report) and fast-tier **actors** (the parallel lens hunters). When your
harness lets you set a different model for sub-agents than for the main agent, you
get the discoverer≠verifier split for free. Both harnesses support it — the
mechanism just differs. Full role→model mapping: `references/model-profiles.md`.

### Hermes Agent (this is the native path)

Hermes has a first-class **delegation model** for sub-agents. Set the main model
to your strong tier and the delegation model to your fast tier in
`~/.hermes/config.yaml`:

```yaml
model:
  default: "DeepSeek-V4-Pro-0813"      # ORCHESTRATOR / judge — the strong tier
  provider: "nous"                          # your provider: nous (Portal) / openrouter / a direct key
  base_url: null

delegation:
  model: "DeepSeek-V4-Flash-0731"      # ACTORS / sub-agents — the fast tier
  provider: "nous"

auxiliary:                                  # side tasks (summarize, compress) — keep them cheap
  compression:
    provider: "auto"                        # "auto" = main model; set to flash to save credits
    model: ""
```

Or set them from the CLI (secrets auto-route to `~/.hermes/.env`, the rest to
`config.yaml`):

```bash
hermes config set model DeepSeek-V4-Pro-0813
hermes config set delegation.model DeepSeek-V4-Flash-0731
```

Use the exact model IDs and provider name your Portal/provider exposes (check with
`hermes models` or the Portal UI). With Nous Portal you authenticate once via
`hermes setup --portal` and credits route to whichever model you pick — no
per-key export needed. Keep the **deep-logic loop (Feynman/State, invariant,
execution-trace) on the main pro model**, not the flash delegation tier — let
delegation carry the breadth actors (`references/model-profiles.md`).

### Claude Code

The orchestrator is the main session model — set it to Opus 4.8 (`/model opus`).
Sub-agents (actors) are dispatched via the Task tool; set their model to Sonnet 5,
either per-dispatch or session-wide with `CLAUDE_CODE_SUBAGENT_MODEL`.

> **Optional — DeepSeek *behind* Claude Code** (not the Hermes path). If you
> specifically want to run the Claude Code CLI but pointed at DeepSeek, that's a
> Claude-Code env-var config, unrelated to Hermes:
> `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`,
> `ANTHROPIC_MODEL=DeepSeek-V4-Pro-0813`, `CLAUDE_CODE_SUBAGENT_MODEL=DeepSeek-V4-Flash-0731`
> (plus your `ANTHROPIC_AUTH_TOKEN`). Most DeepSeek users should just use Hermes
> above instead.

> **On a single model** (no distinct delegation tier available): the split
> collapses harmlessly. Rigor still comes from the **alternating loop** and
> **independent falsification at the gate**, not from model ranking. The tiers
> are an upgrade when you have them, never a requirement.

---

## Tier 1 — Web tools (optional; Strand A acceleration)

### An adaptive, JS-rendering crawler — backs `http_crawl`

Any headless-browser crawler that exports routes/forms/XHR works. Playwright
is a solid, widely available default:

```bash
# Linux / macOS / WSL
pip install playwright && playwright install chromium --with-deps
```
```powershell
# Windows (PowerShell)
pip install playwright
playwright install chromium
```

### Recon CLIs — backs `surface_inventory`, `input_mutation`, `port_scan`

Several of these (`amass`, `subfinder`, `httpx`, `ffuf`, `nuclei`, `gitleaks`)
are Go binaries. **If you have Go installed, `go install <module>@latest`
produces the identical command on WSL and native PowerShell** — that's the
most reliable cross-platform path and the one used below; package-manager
alternatives are given where they exist.

**amass** (subdomain enumeration):
```bash
# Linux / macOS / WSL
brew install amass                    # macOS / Linuxbrew
# or:
go install -v github.com/owasp-amass/amass/v4/...@master
```
```powershell
# Windows (PowerShell) — same Go command, if Go is installed for Windows
go install -v github.com/owasp-amass/amass/v4/...@master
```

**subfinder** (passive subdomain discovery):
```bash
brew install subfinder
# or:
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```
```powershell
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

**httpx** (alive-host / tech probing):
```bash
brew install httpx
# or:
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
```
```powershell
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
```

**ffuf** (content/param fuzzing):
```bash
brew install ffuf
sudo apt install ffuf              # Debian/Ubuntu, recent releases
# or:
go install github.com/ffuf/ffuf/v2@latest
```
```powershell
go install github.com/ffuf/ffuf/v2@latest
```

**gobuster** (content discovery):
```bash
brew install gobuster
sudo apt install gobuster
```
```powershell
go install github.com/OJ/gobuster/v3@latest
```

**wfuzz** (fuzzing, Python-based):
```bash
pip install wfuzz
```
```powershell
pip install wfuzz
```

**nmap** (port scanning):
```bash
brew install nmap
sudo apt install nmap
```
```powershell
choco install nmap
# or: winget install nmap.nmap   (verify the exact id with: winget search nmap)
```

**nuclei** (template-based active scan, `active_scan` fallback):
```bash
brew install nuclei
# or:
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```
```powershell
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

**sqlmap** (`sqli_test`; requires the scope card to allow active testing):
```bash
sudo apt install sqlmap
pip install sqlmap
```
```powershell
pip install sqlmap
# or: choco install sqlmap
```

**trufflehog** / **gitleaks** (`secret_scan`):
```bash
brew install trufflehog gitleaks
# or:
go install github.com/trufflesecurity/trufflehog/v3@latest
go install github.com/gitleaks/gitleaks/v8@latest
```
```powershell
go install github.com/trufflesecurity/trufflehog/v3@latest
go install github.com/gitleaks/gitleaks/v8@latest
# or: choco install gitleaks
```

Absent → recon falls back to `curl` + JS parsing, and the missing pieces
become coverage-debt.

---

## Tier 2 — Burp proxy (optional; you said you have it)

### Burp Suite itself

```bash
# Linux / WSL — snap, or the official .sh installer from portswigger.net
sudo snap install burpsuite
# macOS
brew install --cask burp-suite
```
```powershell
# Windows — the official installer from portswigger.net is the reliable path.
# If you prefer a package manager, search for the current id first:
winget search burp
choco search burpsuite
```

### Java 21 (required to build the MCP bridge from source)

```bash
brew install openjdk@21                          # macOS
sudo apt install openjdk-21-jdk                   # Debian/Ubuntu, WSL
```
```powershell
winget install EclipseAdoptium.Temurin.21.JDK
# verify the id first if this doesn't resolve: winget search temurin
```

### The Burp MCP bridge

Helix drives Burp through an MCP server loaded as a Burp extension. Prefer an
agent-oriented build (newest-first proxy history, readable site map, a full
Repeater send+read loop) over the stock extension, which serves oldest-first
history and truncates responses.

```bash
# Linux / macOS / WSL
git clone <your-chosen-burp-mcp-bridge-repo>
cd <repo>
./gradlew embedProxyJar
# → build/libs/burp-mcp-all.jar
```
```powershell
# Windows (PowerShell) — the Gradle wrapper's Windows batch script
git clone <your-chosen-burp-mcp-bridge-repo>
cd <repo>
.\gradlew.bat embedProxyJar
```

Load the resulting jar in Burp: **Extensions → Add → Java →** select it. Then
point your MCP client at the bridge's local address (commonly
`http://127.0.0.1:9876`).

**Read before using on someone else's target:** some agent-oriented builds
ship with approval prompts **OFF** by default — a connected client can send
requests and read history without asking. Re-enable the prompts for
third-party engagements. Keep the bridge bound to `127.0.0.1`. Full safety
notes: `references/local-tooling.md`.

Absent → `proxy_observation`/`request_replay` fall back to scripted `curl`;
`active_scan`/`oob_observation` become coverage-debt.

---

## Tier 3 — Web3 tools (optional; Strand B verification)

### Foundry — backs `poc_evm` (turns REACHABLE findings into CONFIRMED)

```bash
# Linux / macOS / WSL — the official installer
curl -L https://foundry.paradigm.xyz | bash && foundryup    # forge, cast, anvil
```
```powershell
# Windows — Foundry's official installer targets macOS/Linux. Native Windows
# support is limited/unofficial; run it inside WSL instead (Tier 4), which is
# what the Foundry docs themselves recommend for Windows users.
```

### slither — backs `static_analysis`

```bash
pip install slither-analyzer
```
```powershell
pip install slither-analyzer
```

### echidna / medusa — backs `property_fuzzing`

```bash
# echidna — macOS
brew install echidna
# echidna — Linux / WSL: prebuilt binary from the crytic/echidna GitHub
# releases page, or via Docker:
docker pull ghcr.io/crytic/echidna/echidna

# medusa — Go tool, same command everywhere Go is installed:
go install github.com/crytic/medusa@latest
```
```powershell
# medusa — identical Go command on native Windows:
go install github.com/crytic/medusa@latest
# echidna — no native Windows build; use WSL or Docker Desktop.
```

### halmos — backs `property_fuzzing` (symbolic)

```bash
pip install halmos
```
```powershell
pip install halmos
```

### Non-EVM chain toolchains (install only what a target needs)

```bash
# Rust / Solana toolchain — Linux / macOS / WSL
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install latest && avm use latest

# Move / Aptos
curl -fsSL "https://aptos.dev/scripts/install_cli.py" | python3

# Move / Sui
cargo install --locked --git https://github.com/MystenLabs/sui.git --branch mainnet sui

# Cairo / Starknet
curl --proto '=https' --tlsv1.2 -sSf https://docs.swmansion.com/scarb/install.sh | sh
```
```powershell
# Rust itself installs natively:
winget install Rustlang.Rustup
# anchor/avm then builds the same way via `cargo install` above.

# Solana, Aptos, Sui, and Scarb tooling are Linux-first and least painful
# through WSL — install Rust/the chain CLI inside WSL (Tier 4) rather than
# fighting native Windows builds for these specifically.
```

Absent → findings can still reach REACHABLE by code trace, but a
severity-critical finding without a runnable PoC stays a strong lead, not a
CONFIRMED critical (`references/judging.md`).

---

## Tier 4 — WSL setup (Windows operators)

If you're on Windows, install WSL2 first — several Tier 1/3 tools are either
Linux-only or simply more reliable there.

```powershell
# Run as Administrator, one time:
wsl --install                     # installs WSL2 + Ubuntu by default
# or pick a specific distro:
wsl --install -d Ubuntu-22.04

# Keep the WSL kernel current:
wsl --update

# Enter your WSL environment:
wsl
```

Once inside WSL, it's a normal Linux box — every "Linux / macOS / WSL" command
block above runs verbatim. Helix then **auto-routes**: it tries a tool
natively on PowerShell first, and falls back to `wsl.exe -e bash -lc "<tool>
<args>"` automatically if the native lookup fails, translating Windows paths
to `/mnt/c/...` as needed. Nothing to configure — the full routing rule and
path-translation details are in `references/local-tooling.md`.

**Recommended default:** run the whole Linux-native toolchain (Tier 1 and
Tier 3) inside WSL, and let PowerShell handle only what genuinely runs there
natively (`curl`, the harness itself, `winget`-installed GUI tools like Burp).
One consistent Linux environment beats juggling per-tool Windows ports.

**Burp across the WSL boundary:** Burp normally runs on the **Windows host**
(it's a GUI app), so its MCP bridge listens on `127.0.0.1:9876` from
Windows's perspective. That's reached by the MCP client in your harness, not
by shell tools, so Burp works regardless of where your CLI tools run. If a
WSL-side tool needs to route *through* Burp's proxy, point it at the Windows
host IP from inside WSL — `127.0.0.1` inside WSL2 is the WSL VM, not Windows.

---

## Verify your install

```
/helix --check         # prints the tool roster: what's present, what's debt
```

(Or just drop a scope link — intake writes `.audit/tooling.md` with the
available-vs-absent map on the first run, and every coverage gap lands in the
report's Coverage section.)

Nothing here is a prerequisite for hunting except Tier 0. Everything else
makes Helix faster and its proofs stronger — it never makes the audit possible
or impossible.
