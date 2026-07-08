# ADR-004: Selection of Stateless JWT Authentication

* **Date**: June 30, 2026
* **Status**: Approved

## Context
We need to secure our API endpoints and restrict access to authorized users. We need to decide between stateful sessions (cookie-based) and stateless tokens (JWT).

## Decision
We chose **Stateless JWT (JSON Web Tokens)** for authentication.

## Consequences
* **Positives**:
  - Scalability: The backend does not need to store session state in a database or Redis cache. It simply decodes and verifies the signature of the incoming token.
  - Decoupling: Easily supports multi-origin clients (e.g., mobile apps or third-party integrations in the future).
  - Integrates natively with Supabase Auth, which issues JWTs.
* **Negatives**:
  - Revocation: Since tokens are stateless, they cannot be easily invalidated before their expiration date unless we implement a complex token blacklist.
  - Security: JWTs stored in `localStorage` are vulnerable to Cross-Site Scripting (XSS) attacks. We must ensure robust Content Security Policies (CSP) are in place.
