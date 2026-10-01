# Changelog

All notable changes to Bloomery (app, Docker image and Home Assistant integration) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/krugerhomeassistant/Bloomery/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/krugerhomeassistant/Bloomery/releases/tag/v1.2.0
