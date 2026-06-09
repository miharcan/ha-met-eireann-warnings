# Met Eireann Warnings for Home Assistant

A Home Assistant custom integration that fetches live Met Eireann weather
warnings from the official RSS/CAP feed and exposes them as sensors.

## Overview

This integration uses Met Eireann's active warnings RSS feed as an index, then
fetches linked CAP XML warnings to create structured sensor data for land,
marine, and environmental warnings.

## Features

- Polls official Met Eireann RSS/CAP warning feeds.
- Deduplicates duplicate or near-duplicate warnings.
- Exposes summary and count sensors.
- Supports land, marine, and environmental warning filtering.

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Open the custom repositories menu.
4. Add this repository URL.
5. Select category `Integration`.
6. Install `Met Eireann Warnings`.
7. Restart Home Assistant.
8. Add `Met Eireann Warnings` from Settings → Devices & services.

### Manual installation

1. Copy `custom_components/met_eireann_warnings` into your Home Assistant
   `custom_components` directory.
2. Restart Home Assistant.
3. Add `Met Eireann Warnings` from Settings → Devices & services.

## Configuration

Configure the integration from Home Assistant UI:

- Go to Settings → Devices & services.
- Click Add Integration.
- Search for `Met Eireann Warnings`.
- Complete the one-step form.

Options include:

- Include land warnings
- Include marine warnings
- Include environmental advisories

## Entities

The integration creates these sensor entities:

- `sensor.met_eireann_warnings_warnings`
- `sensor.met_eireann_warnings_warning_count`
- `sensor.met_eireann_warnings_land_warning_count`
- `sensor.met_eireann_warnings_marine_warning_count`
- `sensor.met_eireann_warnings_environmental_warning_count`
- `sensor.met_eireann_warnings_highest_warning_level`
- `sensor.met_eireann_warnings_summary_source`

The `sensor.met_eireann_warnings_warnings` entity includes a `warnings`
attribute with parsed CAP warning data.

## Troubleshooting

- Verify the integration folder is installed in
  `custom_components/met_eireann_warnings`.
- Restart Home Assistant after copying or updating files.
- Check Home Assistant logs for `met_eireann_warnings` or integration errors.
- If the integration is missing from the UI, confirm `manifest.json`
  contains `"config_flow": true` and `config_flow.py` exists.

## Development and testing

Run the parser tests locally:

```bash
cd PATH_TO/ha-met-eireann-warnings
python3 -m pytest -q tests/test_parser.py
```

## License

MIT License. Met Eireann warning data remains subject to Met Eireann's data
terms and attribution requirements.
