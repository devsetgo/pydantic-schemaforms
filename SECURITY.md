# Security Policy

## Supported Versions

Only the latest released version receives security fixes.

| Version | Supported |
| ------- | --------- |
| latest  | yes       |
| older   | no        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities privately via GitHub's
[Security Advisories](https://github.com/devsetgo/pydantic-schemaforms/security/advisories/new)
page (Settings → Security → Advisories → New draft advisory).

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (or a minimal proof-of-concept)
- The version(s) affected

You will receive a response within **7 business days** acknowledging receipt.
We aim to release a fix within **30 days** for confirmed vulnerabilities, sooner
for critical issues.

## Scope

This library's primary security guarantee is **structural XSS protection** via
Python 3.14 t-strings and the `html()` processor in `pydantic_schemaforms.tstring`.
Any bypass of this protection is treated as a critical severity issue.

Out of scope: vulnerabilities in third-party libraries (Pydantic, FastAPI, Flask,
HTMX) — report those upstream.

## Disclosure

We follow **coordinated disclosure**: a CVE / public advisory is published after
a fix is available, or after 90 days from the report date, whichever comes first.
