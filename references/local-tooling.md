# Local Tooling — capabilities, Burp, and PowerShell→WSL routing

Helix binds to **capability names, never product names.** A lens asks for
`http_crawl`; the adapter picks whatever tool provides it, and if none is
present, records **coverage-debt** and continues. This keeps the methodology
stable whether the operator has a full kit or nothing but `curl`.

**The golden rule:** a missing tool is never a silent skip and never a pass. It
is coverage-debt, named in the report (`report-formatting.md` → Coverage
section). Helix says what it couldn't check.

---

## Capability → tool binding

| Capability | Preferred | Fallback | If absent |
|---|---|---|---|
| `http_fetch` | `curl` / harness web-fetch | any HTTP client | coverage-debt (can't fingerprint) |
| `surface_inventory` | `amass`, `subfinder` | cert-transparency search | debt (no subdomain map) |
| `http_crawl` | an **adaptive crawler** (JS-rendered, XHR capture) | `ffuf`/`gobuster` + JS parsing | manual endpoint list |
| `input_mutation` | `ffuf`, `wfuzz` | scripted `curl` loops | debt (no param fuzzing) |
| `secret_scan` | `trufflehog`, `gitleaks` | grep JS/`.env`/`.git` | manual JS read |
| `proxy_observation` | **`mitmproxy`** ✓ (Burp via MCP if wired) | scripted capture | debt (no proxy view) |
| `browser_dynamic` | **harness live-browser + DevTools (Browser Use / CDP)** | manual browser JS | debt (no live-app view) |
| `request_replay` | scripted `curl` / mitmproxy | Burp Repeater if wired | scripted `curl` |
| `active_scan` | **`nuclei`** ✓ | Burp active scan if wired | debt (passive only) |
| `oob_observation` | **`interactsh-client`** ✓ | Burp Collaborator if wired | debt (no blind-vuln confirmation) |
| `sqli_test` | `sqlmap` | manual payloads | manual (active gate required) |
| `port_scan` | **`nmap`** ✓ | `masscan` | debt |
| `contract_read` | **`cast`** ✓, block explorer | web3 RPC call | debt |
| `poc_evm` | **Foundry** (`forge`/`anvil`) ✓ | Hardhat | debt (finding stays REACHABLE, not CONFIRMED) |
| `property_fuzzing` | **`echidna`, `medusa`** ✓ | Foundry invariant tests | debt (no fuzz coverage) |
| `static_analysis` (EVM) | **`slither`** ✓ (context-filtered) | manual read | manual read |
| `sast_source` (backend) | **`semgrep`** ✓ (`--config auto`, filter to reachable) | grep §BACKEND gate | the §BACKEND grep gate |
| `content_discovery` | **`ffuf`** ✓ | `gobuster` | manual endpoint list |

**Active-testing capabilities** (`active_scan`, `sqli_test`, `port_scan`,
brute-force, any on-chain state change on mainnet) require the scope card to
allow active testing (`scope-intake.md`). If the card says passive/testnet-only,
these stay off and are recorded as intentional non-coverage, not debt.

Detect what's present at engagement start (a quick `command -v` / `where` sweep
of the roster), write the available-vs-absent map into `.audit/tooling.md`, and
let the lenses route against it.

**Confirmed present on this operator's host** (verified 2026-08-21, so these are
adapters, not debt): `interactsh-client` (OOB — the one that confirms blind
SSRF/XXE/RCE), `mitmproxy`, `ffuf`, `nmap`, `nuclei`, `semgrep`, `slither`,
`echidna`, `medusa`, and Foundry (`cast`/`anvil`/`forge`). Burp is **not** wired,
and it does not need to be: every capability it would serve has a present
fallback above. The one thing to still stand up per web engagement is an
`interactsh-client` session (`interactsh-client -v`), because blind-vuln
confirmation is gated and unprovable without it — see `web-gates.md`.

`semgrep` is the SAST engine for the §BACKEND source gate (`vm-gates.md`): run
`semgrep --config auto` for the framework's route/authz/injection rules, then
**filter its output through the same VERIFY gate as everything else** — semgrep is
a lead generator, not a finding source, and its default ruleset over-reports.
Treat a semgrep hit exactly like a grep hit: a shape to trace, not a bug to file.

---

## Burp Suite integration

The operator has Burp. Helix drives it through a **Burp MCP bridge** — an MCP
server (loaded as a Burp extension) that exposes the pieces an agent actually
needs on a long engagement. Prefer a bridge that provides:

| MCP tool (typical name) | Capability it serves |
|---|---|
| newest-first proxy history | `proxy_observation` — newest requests first (offset 0 = what you just sent) |
| site map read | `http_crawl` / `surface_inventory` — the discovered URL inventory, incl. spidered-but-unfetched |
| active scan | `active_scan` — starts a Burp audit (Pro only; hypothesis-only until the gate) |
| crawl | `http_crawl` — starts a Burp crawl |
| repeater send + read | `request_replay` — the full send-and-read loop |

The stock/official Burp MCP extension serves oldest-first history and truncates
responses, which is painful on a long engagement; an "agent-oriented" build that
adds newest-first history, a readable site map, and a full Repeater loop is worth
seeking out or building. Whatever bridge you use:

**Two safety facts — hold them:**

1. **Some agent-oriented builds ship with approval prompts OFF by default** and
   config-editing ON — a connected client can send HTTP requests and read proxy
   history *without asking first*. Before pointing Helix at a live third-party
   target, decide deliberately whether that's acceptable; re-enable the prompts if
   in doubt. For your own in-house targets it's a convenience; for someone else's
   program, re-impose Helix's own scope check on every active op regardless.
2. **It binds `127.0.0.1:9876`.** Keep it there. Never expose it on a routable
   interface with approvals disabled.

**Helix's rule on top of Burp:** every active Burp op (`active_scan_url`,
`crawl_url`, a Repeater send to a new host) is checked against the scope card
first — Burp's disabled prompts do not remove Helix's fence. And **a Repeater
"send" is not a concurrency proof**: a race finding needs genuine parallel
requests, not one clicked send (`strands/web-recon.md` → race lens).

Setup is in `INSTALL.md`. If Burp/MCP isn't connected, `proxy_observation` and
`request_replay` fall back to scripted `curl`, and `active_scan`/`oob_observation`
become coverage-debt.

---

## Browser / DevTools dynamic analysis — the primary tool for SPA & web3 frontends

For any target whose frontend does real work in the browser — **casino, perp-DEX,
bridge, marketplace, any web3 app** — the highest-value web findings live in code
`curl`, `ffuf`, and even Burp's proxy **cannot see**:

- the **client JS that builds and signs the transaction** the wallet signs (crossover Seam 4 — frontend injection → wallet drain);
- the **WebSocket price/order feed** the app trusts (Seam 5 — feed manipulation → on-chain mispricing);
- the **SIWE / EIP-712 / JWT handshake** between the web session and the on-chain identity (Seam 6);
- **DOM state, `localStorage`, `sessionStorage`, cookies**, and every script the app actually loads (the supply-chain + secret surface static recon misses).

**Method — `browser_dynamic`.** Drive the running app in a real browser (harness `browser_exec` / Browser Use; DevTools-equivalent via CDP) and observe it the way the user's browser does:

1. Load the live app and click through every real flow (sign-in, deposit, trade, withdraw, claim, admin).
2. Capture the **network surface** — every XHR/`fetch` with full request + response (headers, params, body, status), not just what a crawler finds.
3. Capture **WebSocket frames** — the feed schema, the order flow, what the client trusts unauthenticated.
4. Read **DOM, `localStorage`, `sessionStorage`, cookies** — client-held secrets, signing material, session tokens, permission state.
5. List every **loaded script/service-worker** for the supply-chain + dependency-injection lens.

**This is dynamic observation, not static reading.** Record `.audit/recon/browser-observations.md` — the real request/response/WS-frame/DOM list. Do not guess an endpoint or a request shape; **watch it fire.** Web findings for these targets that are not backed by a live-browser observation are leads, not findings.



Most hunting tools are Linux-native. On Windows, the operator runs the harness
from PowerShell but many tools (`ffuf`, `amass`, `sqlmap`, `nuclei`, `subfinder`,
Foundry, `slither`) live in WSL. Helix routes automatically.

### The routing rule

```
For each tool invocation:
  1. Try it natively on the current shell.
       PowerShell: `where <tool>`  → if found, run it directly.
  2. If NOT found natively (or it errors as a missing/incompatible binary),
     and WSL is available (`wsl.exe -l -q` lists a distro):
       route through WSL:
         wsl.exe -e bash -lc "<tool> <args>"
  3. If neither works → coverage-debt for that tool's capability. Never silently skip.
```

Detect the platform once at start:
- `$env:OS -eq "Windows_NT"` (or the harness reports Windows) → Windows host.
- Probe `wsl.exe -l -q` → note whether WSL + a distro exist, and which.
Write the result to `.audit/tooling.md` so every later call routes without
re-probing.

### Path translation (the thing that bites)

When routing a Windows-side path into a WSL command, translate it:

```
C:\Users\me\target\src   →   /mnt/c/Users/me/target/src
```

Use `wsl.exe wslpath 'C:\path'` to convert, or translate the drive prefix
(`C:\` → `/mnt/c/`, backslashes → forward slashes) directly. Output files a WSL
tool writes under `/mnt/c/...` are visible to PowerShell at the Windows path —
prefer writing tool output to a path under the repo so both sides see it.

### Concrete examples

```powershell
# native first, WSL fallback — subdomain enum
where amass 2>$null
if ($LASTEXITCODE -ne 0) { wsl.exe -e bash -lc "amass enum -passive -d target.com" }

# a Linux tool on a Windows-side wordlist, path-translated
wsl.exe -e bash -lc "ffuf -w /mnt/c/Users/me/wordlists/raft.txt -u https://target.com/FUZZ"

# Foundry PoC for a repo cloned on the Windows side
wsl.exe -e bash -lc "cd $(wsl.exe wslpath 'C:\Users\me\target') && forge test --match-test testExploit -vvv"
```

### Burp across the WSL boundary

Burp typically runs on the **Windows host** (the GUI), so its MCP server is at
`127.0.0.1:9876` on Windows. That's reached by the **MCP client in the harness**,
not by shell tools — so Burp works regardless of where CLI tools run. If a
WSL-side tool needs to route *through* Burp's proxy, point it at the Windows host
IP from WSL (`$(ip route show default | awk '{print $3}')` inside WSL gives the
host), not `127.0.0.1` — inside WSL2, `127.0.0.1` is the WSL VM, not Windows.

### Rule of thumb

- **Prefer WSL for the whole toolchain** when the operator has it — one
  consistent Linux environment, no per-tool PowerShell portability surprises.
  Route everything through `wsl.exe -e bash -lc "..."` and keep paths under
  `/mnt/c/...` or a WSL-home clone.
- **Fall back to PowerShell-native** only for tools that genuinely run there
  (`curl`, harness-native fetch) or when WSL is absent.
- Whatever routes where, record it in `.audit/tooling.md` so the report's
  coverage section is accurate.

---

## No tool? Still audit.

Helix's core — the strands, the alternating loop, the gate, the mental tools — is
markdown and reasoning. It needs **no** tool to read a contract, reason about a
web flow, or write a PoC by hand. Tools accelerate recon and verification; their
absence lowers coverage and is reported honestly, but it never stops the audit.
The methodology runs on judgment; the tools just feed it faster.
