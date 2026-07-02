# Security Architecture

This document describes how authentication, role permissions, and configurations are secured.

## 1. Authentication & Session Security

- **Password Hashing**: Passwords are encrypted before database insertion using `bcrypt` (via `passlib` context).
- **Session Tokens (JWT)**: Authentication is stateless. Session tokens are signed using HMAC-SHA256 with a unique `SECRET_KEY` env variable.
- **Expiration Policy**: JWT tokens are issued with a default expiration time of 7 days, after which clients must re-authenticate.

---

## 2. Role-Based Access Control (RBAC)

FastAPI endpoints enforce role-based routes authorization using the `RoleChecker` dependency injection class:

- **Admin**: Full read-write permission for all organizations, projects, queue settings, and users.
- **Manager**: Full read-write permission for jobs, queues, and projects. Can not edit organization details.
- **Viewer**: Read-only permissions for dashboard, active metrics, jobs list, and logs. Can not submit jobs, modify policies, or re-run DLQ entries.

---

## 3. Data Protection

- **Input Validations**: FastAPI uses Pydantic base validation classes to enforce strict type checking, formatting rules, and email checks, mitigating SQL injection and format exploits.
- **CORS Policies**: Starlette CORS middleware restricts API route actions from untrusted domains.
