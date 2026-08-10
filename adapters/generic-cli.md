# Generic CLI adapter

## Contract

A compatible harness must provide:

- a shell or process runner;
- a persistent case directory;
- a way to launch parallel jobs;
- a way to pass case and graph artifacts;
- a browser, HTTP client, proxy, RPC or simulator capability when required;
- deterministic exit status and captured stdout/stderr.

## Suggested interface

~~~text
ih run --case case.json --mode web
ih run --case case.json --mode chain
ih merge --case case.json --branch branch.json
ih verify --case case.json --finding finding.json
ih report --case case.json
~~~

The commands are an adapter convention. A harness may implement equivalent
operations, but it must preserve the same artifacts and gates.
