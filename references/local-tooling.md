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
| `proxy_observation` | **Burp via MCP** (site map, history) | `mitmproxy` | debt (no proxy view) |
| `request_replay` | **Burp Repeater** (via MCP) | scripted `curl` | scripted `curl` |
| `active_scan` | Burp active scan | `nuclei` | debt (passive only) |
| `oob_observation` | Burp Collaborator | `interactsh` | debt (no blind-vuln confirmation) |
| `sqli_test` | `sqlmap` | manual payloads | manual (active gate required) |
| `port_scan` | `nmap` | `masscan` | debt |
| `contract_read` | `cast`, block explorer | web3 RPC call | debt |
| `poc_evm` | **Foundry** (`forge`) | Hardhat | debt (finding stays REACHABLE, not CONFIRMED) |
| `property_fuzzing` | `echidna`, `medusa` | Foundry invariant tests | debt (no fuzz coverage) |
| `static_analysis` | `slither` (context-filtered) | manual read | manual read |

**Active-testing capabilities** (`active_scan`, `sqli_test`, `port_scan`,
brute-force, any on-chain state change on mainnet) require the scope card to
allow active testing (`scope-intake.md`). If the card says passive/testnet-only,
these stay off and are recorded as intentional non-coverage, not debt.

Detect what's present at engagement start (a quick `command -v` / `where` sweep
of the roster), write the available-vs-absent map into `.audit/tooling.md`, and
let the lenses route against it.

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

## PowerShell → WSL routing (Windows operators)

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
