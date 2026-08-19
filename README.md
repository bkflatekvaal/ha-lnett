# Lnett Tariff for Home Assistant

Custom integration that reads Lnett's public private-customer tariff page and exposes the current published tariff values as Home Assistant sensors.

## v0.1.0

Sensors:
- Current energy tariff (automatically switches between day and night/weekend)
- Binary sensor `Dagtariff` (ON during day tariff, OFF otherwise)
- Energy tariff, day
- Energy tariff, night/weekend
- Electricity consumption tax
- Enova fee
- Capacity tariffs 0–2, 2–5, 5–10, 10–15, 15–20 and 20–25 kW

The integration refreshes the Lnett page once every 24 hours.

## Defensive parsing

The parser searches for semantic labels such as `Energiledd, dag` and `Kapasitetsledd 5 - 10 kW`, rather than relying on CSS classes or table row positions.

A new dataset is accepted only if:
- the tariff validity date is found;
- all expected tariff values are found;
- all values pass sanity checks.

If an update cannot be parsed, Home Assistant's DataUpdateCoordinator marks the update as failed and retains the last successful data.

## Installation for development

Copy `custom_components/lnett` to your Home Assistant `custom_components` directory and restart Home Assistant.

Then:
**Settings → Devices & services → Add integration → Lnett Tariff**

For HACS development, put this project in a GitHub repository and add it to HACS as a custom repository of type Integration.

## Notes

v0.1.0 intentionally does **not** calculate your current capacity tier from consumption data. It only provides the tariff values published by Lnett.

The source page is:
https://www.l-nett.no/nettleie/priser-og-vilkar-privat/

## Tariff period

Lnett defines day tariff as Monday-Friday 06:00-22:00. Night/weekend tariff applies Monday-Friday 22:00-06:00, Saturdays, Sundays and Norwegian public holidays. The `Dagtariff` binary sensor follows these rules and can be used directly as an automation trigger.

## v0.1.2

`Energy tariff` now exposes `Day` and `Night` price attributes, uses measurement state class, and the dynamic entities use consistent English names: `Energy tariff` and `Day tariff`.

## v0.1.3

Adds `Total`: current energy tariff + consumption tax + Enova fee, with Day total and Night total attributes.

## v0.1.4

All numeric tariff sensors now use Home Assistant `state_class: measurement`. The `Day tariff` binary sensor intentionally has no state class.

## v0.1.5

Fix: actually register the `Total` sensor during sensor platform setup.

## v0.1.6

Fix the parser test module loading and remove a duplicate Home Assistant sensor import.

## v0.1.7

Add local Home Assistant brand images with light and dark theme variants.
