# Infrastructure audit

Infrastructure work uses the same case, snapshot, graph, evidence, and
falsification gates as web and chain review. Treat cloud accounts, projects,
subscriptions, regions, CIDRs, DNS zones, repositories, registries, clusters,
identity providers, and third-party services as separate authorization units.

## Minimum inventory

Record:

- domains, DNS zones, nameservers, certificates, CDNs, WAFs, origins, IPs,
  ranges, ports, protocols, and ownership evidence;
- cloud organizations/accounts/projects, regions, IAM principals, roles,
  policies, trust relationships, storage, secrets, keys, queues, and logs;
- container registries, images/digests, clusters, namespaces, workloads,
  service accounts, admission controls, and network policies;
- source repositories, CI/CD workflows, runners, artifacts, deployment roles,
  dependency registries, signatures, and provenance;
- identity providers, federation metadata, redirect/reply URLs, token audiences,
  email domains, SPF/DKIM/DMARC, and recovery paths;
- external vendors and explicit shared-responsibility boundaries.

Passive inventory may identify adjacent assets but never makes them in scope.

## Specialist control matrices

### Cloud IAM and storage

- effective permissions, inherited policy, resource policy, role assumption,
  confused deputy, service-linked identity, and cross-account trust;
- public or broadly shared object storage, snapshots, backups, logs, queues, and
  secrets;
- metadata-service exposure, workload identity, temporary credential scope,
  revocation, and key rotation;
- control-plane versus data-plane authorization and organization guardrails;
- audit logging, deletion protection, recovery, and break-glass authority.

### DNS, TLS, edge, and network

- dangling records and provider-verified takeover preconditions;
- origin exposure, alternate host routing, cache keys, request normalization,
  forwarded-header trust, and CDN/WAF/backend differences;
- certificate identity, protocol/cipher policy, mTLS boundaries, HSTS, and
  redirect scope;
- externally reachable management, database, RPC, monitoring, and debug ports;
- SSRF-reachable internal services and egress boundaries.

Do not claim subdomain takeover from a dangling record alone. Prove that the
referenced provider resource can be safely and lawfully claimed.

### Protocol parsing and APIs

- HTTP/1.1, HTTP/2, and HTTP/3 translation differences;
- request framing, duplicate headers, content length/transfer encoding, proxy
  normalization, and cache behavior;
- gRPC reflection/authentication, method exposure, metadata, streaming limits,
  and transcoding;
- SOAP/XML parser behavior, entity handling, schema validation, and signature
  wrapping;
- WebSocket upgrade/origin/authentication and message authorization.

Desynchronization, cache poisoning, and parser differential tests can affect
other users. Prefer a local replica; require explicit production permission,
unique harmless markers, very low volume, and an immediate stop condition.

### Containers and orchestration

- image provenance, mutable tags, base images, embedded secrets, build context,
  capabilities, seccomp, namespaces, host mounts, and privileged execution;
- Kubernetes RBAC, service-account tokens, admission policy, secrets, network
  policy, API exposure, workload identity, and cross-namespace access;
- cluster-admin, node, registry, and deployment-controller trust paths;
- resource limits, autoscaling, disruption budgets, and availability blast
  radius.

### CI/CD and supply chain

- untrusted pull-request/fork input reaching privileged workflows or runners;
- reusable workflow and action pinning, expression injection, cache/artifact
  poisoning, dependency confusion, and package provenance;
- secret exposure through logs, artifacts, environment, build arguments, or
  attacker-controlled scripts;
- deployment approvals, environment separation, signing, attestations, and
  rollback authority.

Never trigger a privileged workflow with attacker-controlled code unless the
case explicitly authorizes the exact fixture and impact boundary.

### Federated identity and email

- OIDC/SAML issuer, audience, redirect/reply URL, state/nonce, PKCE, signature,
  encryption, claim mapping, tenant, and logout/revocation behavior;
- account linking, invitation, domain claim, just-in-time provisioning, SCIM,
  recovery, and MFA bypass paths;
- SPF/DKIM/DMARC alignment, inbound trust, mailing services, forwarding, and
  password-reset delivery assumptions.

## Evidence and completion

Every infrastructure claim needs provider/resource identity, configuration or
runtime evidence, attacker reachability, a safe control, authoritative impact,
snapshot/time sensitivity, and independent verification. Record unavailable
cloud roles, private network paths, logs, or provider ownership checks as
coverage debt rather than assuming safety.
