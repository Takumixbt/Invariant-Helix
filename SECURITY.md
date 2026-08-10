# Security and responsible use

Invariant Helix is a security-research methodology. Use it only against
systems and environments for which you have explicit authorization.

## Safe defaults

- passive discovery and local validation first;
- no real-fund movement unless the program explicitly permits operator-owned
  test funds and the selected tool can enforce the asset/amount ceiling;
- no arbitrary public PoC execution;
- no credential, token or private-key collection;
- no bypass of rate limits, access controls or bot protections without
  explicit written authorization;
- no destructive scans or database extraction by default;
- disposable identities and test data for active workflows.

The bundled race runner refuses real-fund mode. All public artifacts must use
key- and value-aware redaction; raw tokens, cookies, credentials, private keys,
personal data and non-public target data belong only in restricted evidence.

## Reporting an issue in this repository

Do not include live target data, credentials, exploit payloads or private
program information in a public issue. Use a private channel available to the
maintainer and provide a minimal, sanitized reproduction.

## Methodology limitations

The project cannot guarantee that an audit finds every vulnerability. It is
designed to make assumptions, blocked paths, unverified hypotheses and
coverage gaps explicit.
