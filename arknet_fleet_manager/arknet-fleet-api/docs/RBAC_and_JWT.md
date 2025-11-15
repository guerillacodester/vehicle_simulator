# RBAC Policy and JWT Changes

## Overview
This document describes the Role-Based Access Control (RBAC) policy enforcement and JWT claim structure for Strapi access tiers.

---

## Access Tiers
- **Guest**: Limited access to public resources.
- **Dispatcher**: Access to dispatcher-specific endpoints and actions.
- **Admin**: Full access to all resources and administrative actions.

Access tiers are assigned via the user profile and managed through a join table (`user_profiles_access_tier_lnk`).

---

## RBAC Enforcement
- API endpoints are protected based on the user's access tier.
- On login, the backend resolves the user's tier and injects it into the JWT payload.
- Middleware and controllers check the `tier` claim to allow or deny access.

### Example Policy Logic
- **Guest**: Can access `/public`, forbidden from `/dispatcher` and `/admin`.
- **Dispatcher**: Can access `/dispatcher`, forbidden from `/admin`.
- **Admin**: Can access all endpoints.

---

## JWT Payload Structure
On successful login, the JWT includes:
```json
{
  "id": 123,
  "username": "dispatcher",
  "tier": "Dispatcher",
  // ...other claims
}
```

- The `tier` claim is used for RBAC enforcement throughout the API and GraphQL layers.

---

## Example JWTs
**Guest:**
```json
{
  "id": 101,
  "username": "guest",
  "tier": "Guest"
}
```

**Dispatcher:**
```json
{
  "id": 102,
  "username": "dispatcher",
  "tier": "Dispatcher"
}
```

**Admin:**
```json
{
  "id": 103,
  "username": "admin",
  "tier": "Admin"
}
```

---

## API Behavior
- Requests to forbidden endpoints return HTTP 403 Forbidden.
- Allowed endpoints return HTTP 200 OK.
- JWT must be presented in the `Authorization: Bearer <token>` header.

---

## References
- See `auth.ts` for tier resolution and JWT injection logic.
- See GraphQL extension for tier field exposure.
- See `verify_rbac_policy.py` for standalone verification script.

---

_Last updated: November 15, 2025_
