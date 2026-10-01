# Bloomery for Home Assistant

The **Bloomery** integration brings your cycle from a self-hosted [Bloomery](../README.md) server into Home Assistant: where you are in your cycle, your next period, fertile window, life stage and three colour-coded calendars. Use it for dashboards, gentle reminders and automations.

It reads a private, read-only feed. It never sees symptoms, moods, sex or notes, and it can't change anything in Bloomery.

## Requirements

- A running Bloomery server, version 1.1.0 or newer (1.2.0+ for calendars), that Home Assistant can reach over the network (same LAN, Docker network or Tailscale).
- Home Assistant 2025.9 or newer. 2026.3+ shows the Bloomery icon in Settings.
- [HACS](https://hacs.xyz) to install it.

## Installation

1. In HACS open **⋮ → Custom repositories**, add `https://github.com/krugerhomeassistant/Bloomery` with type **Integration**.
2. Search HACS for **Bloomery**, select **Download**, then restart Home Assistant.
3. In Bloomery go to **Profile → Home Assistant & calendar** and select **Create feed**. Copy the **integration URL** (`http://<server>/api/ha/<token>`).
4. In Home Assistant go to **Settings → Devices & services → Add integration → Bloomery** and paste the URL.

[![Open your Home Assistant instance and start setting up Bloomery.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bloomery)

### Configuration parameters

| Parameter | Description |
|---|---|
| Integration URL | The feed URL from Bloomery's profile. Anything after `?` is ignored. Home Assistant's time zone is sent automatically so "today" matches yours. |

There are no other options. Each Bloomery account can be added once; add more accounts by repeating the steps from that account.

## What you get

One service device, **Bloomery &lt;name&gt;**, with:

### Sensors

| Entity | Example | Notes |
|---|---|---|
| Status | `Ovulation in 3 days` | Same headline as the app's cycle ring. Attributes: `summary`, `state` (`period`, `fertile`, `cycle`, `late`, `due`, `pregnancy`, `empty`). |
| Cycle day | `13` | |
| Phase | `Fertile window` | Enum: menstrual, follicular, fertile, ovulation, luteal. Empty in pregnancy mode. |
| Days until period | `17 d` | |
| Next period | `2026-10-17` | Date. |
| Ovulation | `2026-10-03` | Estimated (or confirmed by temperature). |
| Pregnancy chance | `Medium` | Low / medium / high. |
| Life stage | `Cycle` | Cycle, pregnancy or perimenopause. |
| Pregnancy week | `13` | Disabled by default. |
| Due date | `2027-04-07` | Disabled by default. |
| Cycle length, Period length | `29 d`, `4 d` | Learned averages (diagnostic). |

### Binary sensors

| Entity | On when |
|---|---|
| Period | You're on your period (logged or expected today). |
| Fertile window | Today is in the fertile window. |

### Calendars

Each event type is its own calendar, so each has its own colour. Change a colour under the calendar entity's settings.

| Calendar | Events | Default colour |
|---|---|---|
| Periods | Logged and predicted periods | Pink `#FF4A7D` |
| Fertile windows | Fertile windows | Teal `#3CC4BB` |
| Ovulation | Estimated ovulation days | Purple `#7C5CE0` |

Covers the last 60 days and the next 12 predicted cycles. Calendar colours need Home Assistant 2026.2 or newer.

## How data updates

The integration polls the feed every **15 minutes** and again just after **local midnight**, so the cycle day changes on time. Logging in Bloomery shows up within 15 minutes. To refresh sooner, use the `homeassistant.update_entity` action on any Bloomery entity.

## Examples

Remind you the day before your period is due:

```yaml
automation:
  - alias: "Period tomorrow"
    triggers:
      - trigger: state
        entity_id: sensor.bloomery_mia_days_until_period
        to: "1"
    actions:
      - action: notify.mobile_app_phone
        data:
          title: "🌸 Period likely tomorrow"
          message: "Pack supplies and maybe plan a cosy evening."
```

Warm, soft lighting on period days:

```yaml
automation:
  - alias: "Comfort lighting during period"
    triggers:
      - trigger: time
        at: "19:00:00"
    conditions:
      - condition: state
        entity_id: binary_sensor.bloomery_mia_period
        state: "on"
    actions:
      - action: light.turn_on
        target: { area_id: living_room }
        data: { color_temp_kelvin: 2400, brightness_pct: 40 }
```

Show the status on a dashboard:

```yaml
type: tile
entity: sensor.bloomery_mia_status
```

## Use cases

- Heads-up notifications before a period or the fertile window.
- Comfort routines on period days: heating pad smart plug, warmer lights, quieter evening scenes.
- A shared family calendar showing predicted periods, without sharing any symptoms.
- Pregnancy countdown on a wall tablet (enable *Pregnancy week* and *Due date*).

## Known limitations

- Predictions are estimates from your own logs and are **not contraception**.
- Read-only: you can't log periods or symptoms from Home Assistant.
- Polling only; changes in Bloomery can take up to 15 minutes to appear.
- Home Assistant must reach the exact address in the URL. A URL created while browsing over a Tailscale-only name won't work if Home Assistant can't resolve that name; create the feed while using an address Home Assistant can reach.

## Troubleshooting

| Problem | Fix |
|---|---|
| "That doesn't look like a Bloomery integration URL" | Copy the full URL from Bloomery's profile; it must contain `/api/ha/`. |
| "Can't reach Bloomery at that address" | Open the URL from the Home Assistant host (e.g. `curl <url>`). Check the port, Docker network and Tailscale/DNS. |
| Integration asks to re-authenticate | The feed was turned off or a **New token** was created in Bloomery. Paste the new URL in the prompt. |
| Entities unavailable | Bloomery is down or unreachable. They recover automatically on the next successful update. |
| Wrong cycle day around midnight | Check Home Assistant's time zone (Settings → System → General). |
| Icon missing in HACS | Known HACS bug for integrations that ship their own icon ([hacs/integration#5223](https://github.com/hacs/integration/issues/5223)). Settings → Devices & services shows it on HA 2026.3+. |

For bug reports, download diagnostics (integration ⋮ → **Download diagnostics**). The URL, token and your name are redacted.

## Removal

1. **Settings → Devices & services → Bloomery → ⋮ → Delete**.
2. Optionally uninstall it in HACS and restart Home Assistant.
3. In Bloomery, **Profile → Home Assistant & calendar → Turn off** disables the feed URL.

## Quality

The integration follows Home Assistant's [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) at **Platinum** level; see [`quality_scale.yaml`](../custom_components/bloomery/quality_scale.yaml). Tests run against real Home Assistant with 100% coverage, strict typing (mypy), and hassfest + HACS validation in CI.
