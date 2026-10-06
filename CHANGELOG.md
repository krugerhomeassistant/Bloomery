# Changelog

All notable changes to Bloomery (app, Docker image and Home Assistant integration) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.1.0] - 2026-10-06

### Added
- **My words** (Profile → Preferences): swap any word Bloomery uses for your own, e.g. "period" → "time of the month". It applies everywhere: screens, symptom and mood names, daily insights, notifications, calendar feeds, the partner page and AI replies. Whole words only, capitals are kept, text you typed yourself is never changed.

## [2.0.1] - 2026-10-06

### Changed
- **Afrikaans is now more everyday**: a friendlier, more conversational tone across the app, insights, tips, partner messages, notifications and Home Assistant ("app" instead of "toep", lighter phrasing, a bit of local flavour), while health and safety messages stay clear.

## [2.0.0] - 2026-10-06

### Added
- **Afrikaans** (Profile → Language; new accounts follow the browser language). Everything follows your language: screens, daily insights and recaps, notifications, the partner page, calendar feeds, the doctor's report, dates, quick-log names (Siri / Home Assistant accept Afrikaans names) and the Home Assistant integration. The AI assistant is asked to reply in your language.
- **The cycle ring explains itself**: a legend under the ring on Today (and the partner page) shows the period, fertile window, ovulation day and today with their cycle-day numbers, plus a one-line description of what the ring is.
- Translation tooling: `npm run i18n` and `python -m app.i18n` list missing strings; CI fails on gaps. Guide in CONTRIBUTING.md.

### Fixed
- The status label "Ovulation in" is now translated.

## [1.9.0] - 2026-10-06

### Added
- **Wrist temperature**: Apple Health imports now include Apple Watch overnight wrist temperature, and a daily Shortcut automation (steps in Profile → Shortcuts & automations) can send the latest wrist or basal temperature automatically. Ovulation is confirmed from a sustained rise, which works with wrist readings.
- Quick log accepts unit strings like `°F`/`degC` and wrist-range temperatures; the Home Assistant *Log* action accepts temperatures from 32 °C.

## [1.8.0] - 2026-10-06

### Added
- **Birth control** (Profile → Birth control): pill (21+7, 24+4, continuous, progestin-only), ring, patch, injection, hormonal or copper IUD, implant. Today shows where you are ("Pill day 12", "Remove your ring today", "Injection due in 6 days", IUD string checks, replacement dates), and *Birth control reminders* arrive with your daily notifications on the days something needs doing.
- On hormonal methods, fertile-window and ovulation predictions are hidden (app, calendars, Home Assistant, partner page); bleeds are still predicted.

## [1.7.0] - 2026-10-06

### Added
- **Quick logging with an API key** (Profile → Shortcuts & automations): log a period start, symptoms, moods, flow, temperature or a note from Siri Shortcuts, NFC tags or scripts (`/api/quick/*`). The key can only add logs.
- Home Assistant integration: **Log period start** and **Log** actions (set the API key under the integration's *Configure*), with translated errors and responses.

## [1.6.0] - 2026-10-06

### Added
- **Doctor's report** (Insights → Doctor's report): a printable summary of the last 3–24 months for a GP or gynaecologist (cycle and period lengths, regularity, heavy and spotting days, estimated or temperature-confirmed ovulation, symptom patterns and map, temperature, pill adherence, positive tests, health flags, optional notes). *Print / Save PDF* uses the browser's print dialog; sex and activity logs are never included.
- Code of Conduct (Contributor Covenant 2.1).

## [1.5.0] - 2026-10-06

### Added
- Insights: **cycle length over time** chart (with your average and the typical 21–35 day range) and a **symptom map** showing which symptoms and moods you log on which cycle day, across your cycles.

## [1.4.0] - 2026-10-06

### Added
- Unlock with Face ID, Touch ID, fingerprint or Windows Hello (WebAuthn passkeys) as an alternative to the PIN; manage devices under Profile → App lock.
- Native push notifications to your phone or computer (Web Push with VAPID, encrypted payloads), alongside ntfy / Gotify / Home Assistant / Discord. Expired devices are cleaned up automatically.

### Fixed
- A Home Assistant integration test depended on the current date.

## [1.3.0] - 2026-10-06

### Added
- Backups: nightly consistent snapshots in `/data/backups` with retention, *Back up now*, download, and restore from a server backup or an uploaded file (a safety copy is taken first).
- Optional backup encryption with a passphrase (AES-256-GCM, Argon2id key derivation).
- Google Drive backups: upload to a *Bloomery backups* folder (`drive.file` scope), cloud retention, and restore straight from Drive (also on a fresh install).

## [1.2.1] - 2026-10-01

### Changed
- Docker image now runs on Python 3.14 (backend tests run on 3.14 in CI too).
- Frontend type-checking uses TypeScript 7 (native compiler, ~4.5× faster builds).

## [1.2.0] - 2026-10-01

### Added
- Home Assistant integration: **Periods**, **Fertile windows** and **Ovulation** calendars with app-matching default colours (changeable per calendar, HA 2026.2+).
- Home Assistant integration: re-authentication flow when the feed link is turned off or regenerated, diagnostics download (token redacted), translated error messages.
- Calendar feed: `?type=period|fertile|ovulation` to subscribe to each event type separately (separate colours in Google/Apple/Outlook).
- Integration guide: [docs/home-assistant.md](https://github.com/krugerhomeassistant/Bloomery/blob/main/docs/home-assistant.md). The integration meets the Home Assistant Quality Scale at Platinum level (self-assessed).
- Tagged GitHub releases with notes and a `bloomery.zip` for HACS; version bump script; Dependabot; ruff lint/format; mypy strict for the integration; 100% integration test coverage.

### Changed
- Integration code split into `api`, `coordinator` and `entity` modules; *Pregnancy week* and *Due date* sensors are disabled by default.

## [1.1.0] - 2026-09-30

### Added
- Home Assistant custom integration (HACS) with config flow, reconfigure and 14 entities, replacing the pasted YAML.

### Changed
- App lock only asks for the PIN after being away for a chosen time (1 minute to 4 hours, default 15 minutes); 10 wrong tries before sign-out.

## [1.0.0] - 2026-09-30

### Added
- Life stages: pregnancy mode (week, due date, baby size, trimester tips) and perimenopause mode (wider predictions, days since period, 12-month marker), new symptoms.

## [0.9.0] - 2026-09-30

### Added
- Optional app lock PIN.

### Fixed
- Deleting an account now also deletes notes, share/HA links and recaps.

## [0.8.0] - 2026-09-30

### Added
- Home Assistant sensor feed and iCalendar feed; streaming AI chat replies.

## [0.7.0] - 2026-09-30

### Added
- Partner sharing link; learned cycle values shown in Profile.

## [0.6.0] - 2026-09-30

### Added
- AI cycle recaps; Apple Health import.

## [0.5.0] - 2026-09-30

### Added
- Login throttling, security headers, import from Flo, Clue and CSV.

## [0.4.0] - 2026-09-30

### Added
- Notifications via ntfy, Gotify, Home Assistant and Discord; MIT license.

## [0.3.0] - 2026-09-30

### Added
- Daily feed: symptom forecasts, milestones, recaps and tips.

## [0.2.0] - 2026-09-30

### Added
- In-app AI provider settings.

## [0.1.0] - 2026-09-30

### Added
- First release: cycle tracking, predictions, insights, AI assistant, Docker image.

[Unreleased]: https://github.com/krugerhomeassistant/Bloomery/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/krugerhomeassistant/Bloomery/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.9.0...v2.0.0
[1.9.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/krugerhomeassistant/Bloomery/releases/tag/v1.2.0
