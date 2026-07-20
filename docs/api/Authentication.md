# Authentication API

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Authentication API |
| Version | 2.0 |
| Status | Approved |
| Base Path | /api/v1/auth |
| Related Documents | API-Overview.md, Functional-Requirements.md, Business-Rules.md |

---

# Purpose

This document defines all authentication and authorization endpoints for AI Job Agent Version 2.

Authentication is responsible for:

- User registration
- Login
- Logout
- Token refresh
- Password management
- Account management
- Session validation

---

# Authentication Strategy

The application uses:

- JWT Access Tokens
- Refresh Tokens
- HTTPS
- Secure password hashing
- Role-based authorization (future)

---

# Authentication Flow

```text
User
 │
 ▼
Login
 │
 ▼
Authentication API
 │
 ▼
Validate Credentials
 │
 ▼
Issue Tokens
 │
 ▼
Authenticated Requests
 │
 ▼
Refresh Token (when needed)
```

---

# Endpoints Overview

| Method | Endpoint | Purpose |
|---------|----------|----------|
| POST | /register | Create account |
| POST | /login | User login |
| POST | /logout | Logout |
| POST | /refresh | Refresh access token |
| GET | /me | Current user |
| PATCH | /me | Update account |
| POST | /change-password | Change password |
| POST | /forgot-password | Request password reset |
| POST | /reset-password | Complete password reset |
| DELETE | /me | Delete account |

---

# POST /register

## Purpose

Create a new user account.

### Authentication

Not required.

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Validation

- Email required
- Email must be unique
- Valid email format
- Password must satisfy password policy
- First name required
- Last name required

### Success Response

**201 Created**

```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com"
  },
  "message": "Account created successfully."
}
```

### Error Responses

| Status | Reason |
|---------|--------|
|400|Invalid request|
|409|Email already exists|
|422|Validation error|

---

# POST /login

## Purpose

Authenticate a user.

### Authentication

Not required.

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

### Success Response

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

### Errors

| Status | Reason |
|---------|--------|
|401|Invalid credentials|
|423|Account locked (if implemented)|
|429|Rate limited|

---

# POST /logout

## Purpose

Terminate the current authenticated session.

### Authentication

Required.

### Success

**204 No Content**

---

# POST /refresh

## Purpose

Issue a new access token using a valid refresh token.

### Authentication

Refresh token required.

### Request

```json
{
  "refresh_token": "..."
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "expires_in": 3600
  }
}
```

### Errors

- Invalid refresh token
- Expired refresh token
- Revoked refresh token

---

# GET /me

## Purpose

Return the authenticated user's account information.

### Authentication

Required.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "..."
  }
}
```

---

# PATCH /me

## Purpose

Update editable account fields.

### Authentication

Required.

### Editable Fields

- First name
- Last name
- Preferred language (future)
- Time zone (future)

Email changes should follow a separate verification workflow if supported.

---

# POST /change-password

## Purpose

Change the authenticated user's password.

### Authentication

Required.

### Request

```json
{
  "current_password": "...",
  "new_password": "..."
}
```

### Validation

- Current password must be correct.
- New password must satisfy password policy.
- New password must differ from current password.

---

# POST /forgot-password

## Purpose

Initiate a password reset.

### Authentication

Not required.

### Request

```json
{
  "email": "user@example.com"
}
```

### Behavior

To reduce account enumeration risk, the response should be consistent regardless of whether the email exists.

---

# POST /reset-password

## Purpose

Complete the password reset using a valid reset token.

### Request

```json
{
  "token": "...",
  "new_password": "StrongPassword123!"
}
```

### Validation

- Reset token valid
- Reset token not expired
- Password satisfies password policy

---

# DELETE /me

## Purpose

Delete the authenticated user's account.

### Authentication

Required.

### Business Rules

- Confirm user intent before deletion.
- Define whether deletion is soft or permanent according to system policy.
- Associated data retention must follow documented retention requirements.

### Success

**204 No Content**

---

# Password Policy

Passwords should:

- Meet the configured minimum length.
- Include a mix of character types where required by policy.
- Avoid common or easily guessed passwords.
- Be stored only as secure password hashes.

---

# Authorization

All endpoints except:

- Register
- Login
- Forgot Password
- Reset Password

require authentication.

---

# Rate Limiting

Rate limiting should be applied to:

- Login
- Register
- Forgot Password
- Reset Password
- Refresh Token

---

# Security Requirements

Authentication services shall:

- Use HTTPS.
- Never store plaintext passwords.
- Validate all input.
- Protect against brute-force attacks where appropriate.
- Record security-relevant audit events.
- Avoid exposing sensitive information in error messages.

---

# Audit Events

The following events should be recorded:

- Registration
- Login success
- Login failure
- Logout
- Password change
- Password reset request
- Password reset completion
- Account deletion

Each audit event should include:

- Timestamp
- User ID (when available)
- Event type
- Outcome
- Correlation ID (if available)

---

# Error Codes

| Code | Description |
|------|-------------|
|AUTH_INVALID_CREDENTIALS|Incorrect email or password|
|AUTH_TOKEN_EXPIRED|Access token expired|
|AUTH_TOKEN_INVALID|Invalid token|
|AUTH_REFRESH_INVALID|Invalid refresh token|
|AUTH_ACCOUNT_LOCKED|Account locked|
|AUTH_PASSWORD_WEAK|Password does not satisfy policy|
|AUTH_EMAIL_EXISTS|Email already registered|
|AUTH_UNAUTHORIZED|Authentication required|
|AUTH_FORBIDDEN|Insufficient permissions|

---

# Related Documents

- API-Overview.md
- Functional-Requirements.md
- Business-Rules.md
- Security-Architecture.md
- Threat-Model.md

---

End of Document