# CSRF Protection

This guide explains how CSRF works with pydantic-schemaforms, when to use it, and how to configure it safely in production.

## What CSRF Is

Cross-Site Request Forgery (CSRF) is an attack where a malicious site causes a user browser to submit a request to your app while the user is authenticated.

Typical risk pattern:

1. Your app uses cookie-based auth/session.
2. A browser automatically sends those cookies with cross-site requests.
3. An attacker tricks a user into submitting a state-changing request (`POST`, `PUT`, `DELETE`, etc.).

CSRF protection adds an unguessable token that must be present and valid for each state-changing form submission.

## How pydantic-schemaforms Uses CSRF

pydantic-schemaforms renders HTML forms and can include a hidden CSRF field. Your application code is responsible for:

1. Generating a token.
2. Storing/verifying token state (for example, in server-side session storage).
3. Rejecting invalid submissions.

The library intentionally does not own your trust boundary.

## CSRF Modes

`csrf_mode` controls form rendering behavior:

1. `off`: do not render a CSRF field.
2. `field-only`: render CSRF field without requiring a provider.
3. `required-provider`: require a token provider and render token field.

You can pass either:

1. the string value (for example `"required-provider"`), or
2. the enum value (`CSRFMode.REQUIRED_PROVIDER`).

Important production guidance:

1. Prefer `required-provider` for real security.
2. `field-only` is compatibility/migration-oriented and is intentionally restricted:
   - explicit `csrf_mode="field-only"` is only allowed with `debug=True`.
3. Backward compatibility remains for legacy `include_csrf=True` behavior.

## Parameters

Relevant render options:

1. `csrf_mode`: one of `off`, `field-only`, `required-provider`.
2. `csrf_token_provider`: token string or callable returning a token string.
3. `csrf_field_name`: hidden input name (default `csrf_token`).

Example:

```python
from pydantic_schemaforms import CSRFMode

form_html = await render_form_html_async(
    LoginForm,
    form_data=form_data,
    errors=errors,
    submit_url="/login",
    csrf_mode=CSRFMode.REQUIRED_PROVIDER,
    csrf_token_provider=csrf_token,
    csrf_field_name="csrf_token",
)
```

## FastAPI Setup (Recommended Pattern)

```python
import hmac
import secrets

from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="change-me")

CSRF_SESSION_KEY = "login_csrf_token"


def issue_csrf_token(request: Request) -> str:
    token = secrets.token_urlsafe(32)
    request.session[CSRF_SESSION_KEY] = token
    return token


def verify_csrf_token(request: Request, submitted_token: str | None) -> bool:
    expected = request.session.get(CSRF_SESSION_KEY)
    if not expected or not submitted_token:
        return False
    return hmac.compare_digest(str(expected), str(submitted_token))
```

Flow:

1. On `GET`: issue token and render form with `csrf_mode="required-provider"`.
2. On `POST`: extract submitted token, verify, reject with `403` if invalid.
3. On success: rotate/remove token.

## Flask Setup (Equivalent Pattern)

Use Flask session storage and the same issue/verify steps:

1. generate token on `GET`.
2. render with `required-provider`.
3. verify on `POST` before validation.

## When CSRF Applies (And When It Usually Does Not)

CSRF usually applies:

1. Browser-based forms.
2. Cookie/session auth.
3. State-changing endpoints.

CSRF often not applicable:

1. Pure machine-to-machine APIs using bearer tokens in `Authorization` header.
2. Non-browser clients that do not auto-send ambient cookies.
3. Read-only endpoints (`GET`) with no state changes.

Even when CSRF may be less relevant, keep standard API authz/authn controls in place.

## Security Benefits

Using CSRF tokens helps:

1. block cross-site forged submissions.
2. ensure request intent from pages your app rendered.
3. reduce account/action takeover risk in session-based browser workflows.

## Logging Notes

By default, CSRF validation in example integrations surfaces user-facing errors but does not log token values.

Best practice:

1. never log raw CSRF tokens.
2. log only outcome/context (for example, `csrf_failed`, route, request id, user id if available).

## Production Checklist

1. Use `csrf_mode="required-provider"`.
2. Verify token before processing form payload.
3. Use constant-time comparison (`hmac.compare_digest`).
4. Rotate tokens appropriately.
5. Keep session secret strong and private.
6. Use HTTPS in production.
7. Avoid token leakage in logs.
