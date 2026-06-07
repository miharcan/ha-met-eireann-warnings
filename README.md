# Met Eireann Warnings for Home Assistant

An open-source Home Assistant custom integration for active Met Eireann weather
warnings, including marine Small Craft warnings, using the official RSS and CAP
XML feeds.

https://www.met.ie/warningsxml/rss.xml

The integration uses RSS as the active-warning index, then fetches the linked
CAP XML for structured warning fields. This matters because the live RSS feed
can include marine warnings such as Small Craft warnings, while the land JSON
endpoint can miss those.

## Entities

The integration creates these sensors:

- `sensor.met_eireann_warnings_warnings`
- `sensor.met_eireann_warnings_warning_count`
- `sensor.met_eireann_warnings_land_warning_count`
- `sensor.met_eireann_warnings_marine_warning_count`
- `sensor.met_eireann_warnings_environmental_warning_count`
- `sensor.met_eireann_warnings_highest_warning_level`
- `sensor.met_eireann_warnings_warnings_summary_source`

The main warnings sensor exposes a `warnings` attribute containing the parsed
CAP data for each active warning.

## Data Attribution

Data is provided by Met Eireann.

Warning `headline` and `description` fields are exposed unchanged from Met
Eireann CAP data. If you use Home Assistant Assist, OpenAI, or another LLM to
summarise the warnings, keep the generated text separate from the original
warning fields.

## Duplicate Handling

Met Eireann RSS can occasionally contain duplicate or near-duplicate warning
items. This integration deduplicates warnings by:

1. CAP identifier or normalized CAP link.
2. Matching category, event, level, headline, description, area, onset minute,
   and expiry minute.

Collapsed duplicates are recorded on the remaining warning as
`duplicate_count`, `duplicate_identifiers`, and `duplicate_links`.

## Installation

### HACS

Until this is added to the default HACS repository list, install it as a custom
repository:

1. Open HACS.
2. Go to Integrations.
3. Open the custom repositories menu.
4. Add this repository URL.
5. Select category `Integration`.
6. Install `Met Eireann Warnings`.
7. Restart Home Assistant.
8. Add `Met Eireann Warnings` from Settings > Devices & services.

### Manual

Copy `custom_components/met_eireann_warnings` into your Home Assistant
`custom_components` directory, restart Home Assistant, then add
`Met Eireann Warnings` from Settings > Devices & services.

## Dashboard Card

This compact Markdown card shows land and marine warnings only, hides
environmental advisories, uses the official Met Eireann headline and
description text, and shows the CAP warning validity window.

```yaml
type: markdown
content: |
  {% set warnings = state_attr('sensor.met_eireann_warnings_warnings', 'warnings') or [] %}
  {% set wanted = warnings | rejectattr('category', 'eq', 'Environmental') | list %}
  {% set marine = wanted | selectattr('category', 'eq', 'Marine') | list %}
  {% set land = wanted | selectattr('category', 'eq', 'Land') | list %}

  # Met Eireann Warnings

  {% if wanted | count == 0 %}
  No active land or marine warnings.
  {% else %}

  {% for category, items in [('Land', land), ('Marine', marine)] %}
  {% if items | count > 0 %}

  ## {{ category }}

  {% for warning in items %}
  ---

  ### {{ warning.headline or warning.title }}

  **{{ warning.level | title }}**{% if warning.onset or warning.expires %} · {{ as_timestamp(warning.onset) | timestamp_custom('%d %b %H:%M', true) }} to {{ as_timestamp(warning.expires) | timestamp_custom('%d %b %H:%M', true) }}{% endif %}
  {{ warning.description }}

  {% endfor %}
  {% endif %}
  {% endfor %}

  <small>Data provided by Met Eireann.</small>
  {% endif %}
```

## AI Summary Example

The integration does not call an LLM directly. Use Home Assistant to summarise
the structured data:

```yaml
action: conversation.process
data:
  text: >
    Summarise these Met Eireann warnings for a household in Ireland.
    Separate land warnings from marine warnings.
    For marine warnings, mention that they mainly matter for boating or coastal activity.
    Keep the answer short and practical.

    {{ state_attr('sensor.met_eireann_warnings_warnings', 'warnings') }}
response_variable: ai_warning_summary
```

## Licence

Integration code is MIT licensed. Met Eireann warning data remains subject to
Met Eireann's data terms and attribution requirements.
