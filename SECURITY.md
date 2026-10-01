# Security policy

Bloomery stores health data, so security reports are taken seriously.

## Reporting a vulnerability

Please **don't open a public issue**. Report it privately via
[GitHub security advisories](https://github.com/krugerhomeassistant/Bloomery/security/advisories/new).
You'll get a reply within a week, and a fix in the next release for confirmed issues.

## Supported versions

Only the latest release receives fixes. Update with `docker compose pull && docker compose up -d`.

## Design notes

- All data stays in your SQLite file (`/data`); nothing is sent anywhere unless you configure a cloud AI provider or notifications.
- Passwords and PINs are hashed with Argon2; logins are throttled per IP.
- Share, Home Assistant and calendar links are random read-only tokens that never expose symptoms, moods, sex or notes, and can be revoked at any time.
- Run Bloomery behind HTTPS (or a private network such as Tailscale) when it's reachable from outside your home.
