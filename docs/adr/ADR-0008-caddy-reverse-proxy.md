# ADR-0008: Caddy over nginx for reverse proxy

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The production deployment needs a reverse proxy that handles TLS termination, HTTP→HTTPS redirects, gzip, and security headers. Options: nginx, Caddy, or HAProxy.

## Decision

We will use **Caddy 2** as the outer reverse proxy. nginx is still used as the static file server for the React SPA (inside `frontend/Dockerfile`), but Caddy sits in front of everything.

Caddyfile (minimal):
```
{$DOMAIN} {
    reverse_proxy /api/* api:8000
    reverse_proxy /* web:80
}
```

## Consequences

- **Good:** One line of configuration gives automatic Let's Encrypt TLS with HTTP→HTTPS redirect and auto-renewal.
- **Good:** No manual `certbot` cron or DNS challenge needed.
- **Bad:** Caddy's ACME challenges require port 80 and 443 to be reachable from the public internet. This is acceptable for our EC2 deployment.
- **Risks:** Caddy is less battle-tested than nginx for very high traffic, but our scale does not require nginx-level performance.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| nginx + certbot | Manual cert renewal; extra cron job; more config lines |
| Traefik | More complex for single-service deployment; Docker label config is overkill |
| AWS ALB | Adds cost and external dependency; not in scope for single-EC2 MVP |

## References

- `00_MASTER_PLAN.md §0.6, §0.7 Decision #1`
- `04_DEVOPS_LLD.md §Containers`
