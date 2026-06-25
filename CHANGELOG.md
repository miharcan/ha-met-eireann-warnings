# Changelog

## v0.2.0

### Added

- Generic display fields on each warning:
  - `event_clean`
  - `display_title`
  - `display_line`
  - `display_summary`
  - `display_impacts`
  - `display_risk`
  - `awareness_type`
  - `awareness_level`
- Impact extraction from Met Eireann description sections such as
  `Potential impacts:` and `Possible impacts:`.
- Concise dashboard card example in the README.

### Changed

- Summary text now uses the generic display fields.
- Official Met Eireann `headline`, `description`, and `instruction` fields are
  still preserved unchanged.

### Verified

- Parser and compile checks pass.
- Live RSS/CAP smoke test works with current land and marine warnings.

## v0.1.0

Initial HACS custom integration release.

- RSS-first warning polling.
- CAP XML parsing.
- Land, marine, and environmental warning counts.
- Highest warning level sensor.
- Warning deduplication.
