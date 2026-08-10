# HTTP CLI adapter

## Role

Provide reproducible, scriptable requests independent of browser UI or proxy
state. Suitable for controls, replay, method/content-type comparison and
minimal proof requests.

## Request record

Record method, normalized URL, headers with secrets redacted, body shape,
identity, state, expected signal, response summary, timing and evidence path.

## Rules

Start with a single control request. Do not change multiple variables while
triaging. Apply case allowlists and rate budgets. Avoid insecure TLS options,
destructive methods and real data unless explicitly permitted.

## Output

Emit one observation per request and a summary of changed security-relevant
fields. A status-code difference alone is a hypothesis; pair it with
authorization and side-effect evidence.
