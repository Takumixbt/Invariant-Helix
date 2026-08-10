# Fuzzer adapter

## Role

Use ffuf, wfuzz, gobuster, ZAP, nuclei or equivalent tools for narrow,
hypothesis-driven candidate generation.

## Admission checklist

- target and route are in scope;
- request volume and rate are within limits;
- input location and expected signal are documented;
- false-positive controls exist;
- output is captured and redacted;
- no database dumping, destructive payload or bypass behavior is enabled by
  default.

## Interpretation

Fuzzer output is a candidate observation. Verify content-length, reflection,
authorization, state change, timing and error differences against a baseline.
Do not call a route vulnerable because a template or payload matched.
