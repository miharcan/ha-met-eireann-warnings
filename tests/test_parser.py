from importlib import util
from pathlib import Path
import sys
import types

PACKAGE = "custom_components.met_eireann_warnings"
ROOT = Path(__file__).resolve().parents[1]

package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "custom_components" / "met_eireann_warnings")]
sys.modules[PACKAGE] = package

for module_name in ("const", "parser"):
    spec = util.spec_from_file_location(
        f"{PACKAGE}.{module_name}",
        ROOT / "custom_components" / "met_eireann_warnings" / f"{module_name}.py",
    )
    module = util.module_from_spec(spec)
    sys.modules[f"{PACKAGE}.{module_name}"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)

parser = sys.modules[f"{PACKAGE}.parser"]

build_summary_source = parser.build_summary_source
build_summary_state = parser.build_summary_state
clean_event = parser.clean_event
deduplicate_warnings = parser.deduplicate_warnings
highest_level = parser.highest_level
parse_cap = parser.parse_cap
parse_rss = parser.parse_rss
split_description_and_impacts = parser.split_description_and_impacts
warning_counts = parser.warning_counts


RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Small Craft warning from Malin Head to Howth Head to Mizen Head</title>
      <link>https://cap.met.ie//marine-1.xml</link>
      <description>South to southwest winds will reach force 6 or 7 at times</description>
      <category>Marine</category>
      <guid>https://cap.met.ie//marine-1.xml</guid>
      <pubDate>Sun, 07 Jun 2026 00:25:01 GMT</pubDate>
    </item>
    <item>
      <title>Small Craft warning from Malin Head to Howth Head to Mizen Head</title>
      <link>https://cap.met.ie/marine-duplicate.xml</link>
      <description>South to southwest winds will reach force 6 or 7 at times</description>
      <category>Marine</category>
      <guid>https://cap.met.ie/marine-duplicate.xml</guid>
      <pubDate>Sun, 07 Jun 2026 00:30:01 GMT</pubDate>
    </item>
    <item>
      <title>Yellow Rain Warning</title>
      <link>https://cap.met.ie/land-1.xml</link>
      <description>Heavy rain at times.</description>
      <category>Weather</category>
      <guid>https://cap.met.ie/land-1.xml</guid>
      <pubDate>Sun, 07 Jun 2026 01:00:01 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


MARINE_CAP = """<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>{identifier}</identifier>
  <sender>forecasts@met.ie</sender>
  <sent>{sent}</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <language>en-GB</language>
    <category>Met</category>
    <event>Small Craft</event>
    <responseType>Monitor</responseType>
    <urgency>Immediate</urgency>
    <severity>Moderate</severity>
    <certainty>Likely</certainty>
    <effective>2026-06-07T05:02:42+01:00</effective>
    <onset>2026-06-07T05:02:35+01:00</onset>
    <expires>2026-06-08T00:00:00+01:00</expires>
    <senderName>Met Eireann</senderName>
    <headline>Small Craft warning from Malin Head to Howth Head to Mizen Head</headline>
    <description>South to southwest winds will reach force 6 or 7 at times</description>
    <instruction></instruction>
    <parameter>
      <valueName>awareness_type</valueName>
      <value>1; Wind</value>
    </parameter>
    <parameter>
      <valueName>awareness_level</valueName>
      <value>2; yellow; Moderate</value>
    </parameter>
    <area>
      <areaDesc>from Malin Head to Howth Head to Mizen Head</areaDesc>
      <geocode>
        <valueName>EMMA_ID</valueName>
        <value>EI807</value>
      </geocode>
    </area>
  </info>
</alert>
"""


LAND_CAP = """<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>land-1</identifier>
  <sent>2026-06-07T06:00:00+01:00</sent>
  <info>
    <category>Met</category>
    <event>Rain</event>
    <urgency>Expected</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <effective>2026-06-07T06:00:00+01:00</effective>
    <onset>2026-06-07T09:00:00+01:00</onset>
    <expires>2026-06-07T18:00:00+01:00</expires>
    <headline>Orange Rain Warning</headline>
    <description>Heavy rain at times.

Potential impacts:
- Localised flooding
- Poor visibility
- Hazardous driving conditions</description>
    <parameter>
      <valueName>awareness_level</valueName>
      <value>3; orange; Severe</value>
    </parameter>
    <area>
      <areaDesc>Ireland</areaDesc>
      <geocode>
        <valueName>EMMA_ID</valueName>
        <value>EI01</value>
      </geocode>
    </area>
  </info>
</alert>
"""


def test_parse_rss_normalizes_links_and_categories():
    items = parse_rss(RSS)

    assert len(items) == 3
    assert items[0].link == "https://cap.met.ie/marine-1.xml"
    assert items[0].category == "Marine"
    assert items[2].category == "Land"


def test_parse_cap_keeps_original_warning_text_and_marine_category():
    item = parse_rss(RSS)[0]
    warning = parse_cap(
        MARINE_CAP.format(
            identifier="marine-1", sent="2026-06-07T05:02:42+01:00"
        ),
        item,
    )

    assert warning.category == "Marine"
    assert warning.event == "Small Craft"
    assert warning.level == "yellow"
    assert (
        warning.headline
        == "Small Craft warning from Malin Head to Howth Head to Mizen Head"
    )
    assert warning.description == (
        "South to southwest winds will reach force 6 or 7 at times"
    )
    assert warning.geocodes == ["EI807"]
    assert warning.awareness_type == "1; Wind"
    assert warning.awareness_level == "2; yellow; Moderate"
    assert warning.event_clean == "Small Craft"
    assert warning.display_title == (
        "Small Craft warning from Malin Head to Howth Head to Mizen Head"
    )
    assert warning.display_line == "Yellow · 07 Jun 05:02 to 08 Jun 00:00"
    assert warning.display_summary == (
        "South to southwest winds will reach force 6 or 7 at times"
    )
    assert warning.display_impacts == []
    assert warning.display_risk == "Moderate · Immediate · Likely"


def test_deduplicate_warnings_collapses_near_duplicate_content():
    items = parse_rss(RSS)
    warnings = [
        parse_cap(
            MARINE_CAP.format(
                identifier="marine-1", sent="2026-06-07T05:02:42+01:00"
            ),
            items[0],
        ),
        parse_cap(
            MARINE_CAP.format(
                identifier="marine-duplicate",
                sent="2026-06-07T05:03:00+01:00",
            ),
            items[1],
        ),
        parse_cap(LAND_CAP, items[2]),
    ]

    deduped = deduplicate_warnings(warnings)

    assert len(deduped) == 2
    marine = next(warning for warning in deduped if warning.category == "Marine")
    assert marine.duplicate_count == 1
    assert marine.duplicate_identifiers == ["marine-duplicate"]


def test_counts_highest_level_and_summary_source():
    items = parse_rss(RSS)
    warnings = deduplicate_warnings(
        [
            parse_cap(
                MARINE_CAP.format(
                    identifier="marine-1", sent="2026-06-07T05:02:42+01:00"
                ),
                items[0],
            ),
            parse_cap(LAND_CAP, items[2]),
        ]
    )

    assert warning_counts(warnings) == {
        "total": 2,
        "land": 1,
        "marine": 1,
        "environmental": 0,
    }
    assert highest_level(warnings) == "orange"
    assert build_summary_state(warnings) == (
        "Met Eireann: 2 active warnings; 1 land, 1 marine; highest orange."
    )
    summary_source = build_summary_source(warnings)
    assert "Breakdown: 1 land, 1 marine, 0 environmental." in summary_source
    assert "Marine:" in summary_source
    assert (
        "- Small Craft warning from Malin Head to Howth Head to Mizen Head - "
        "Yellow · 07 Jun 05:02 to 08 Jun 00:00"
        in summary_source
    )
    assert "Detail: South to southwest winds will reach force 6 or 7 at times" in (
        summary_source
    )
    assert "Impacts: Localised flooding, Poor visibility" in summary_source


def test_display_fields_are_generic_for_land_impacts():
    item = parse_rss(RSS)[2]
    warning = parse_cap(LAND_CAP, item)

    assert warning.description.startswith("Heavy rain at times.")
    assert "Potential impacts:" in warning.description
    assert warning.event_clean == "Rain"
    assert warning.display_title == "Orange Rain Warning"
    assert warning.display_line == "Orange · Ireland · 07 Jun 09:00 to 07 Jun 18:00"
    assert warning.display_summary == "Heavy rain at times."
    assert warning.display_impacts == [
        "Localised flooding",
        "Poor visibility",
        "Hazardous driving conditions",
    ]
    assert warning.display_risk == "Severe · Expected · Likely"


def test_description_split_and_event_cleaning_are_generic():
    summary, impacts = split_description_and_impacts(
        "Thunderstorms likely. Possible impacts:\n"
        "- Localised flooding\n"
        "- Lightning damage"
    )

    assert summary == "Thunderstorms likely."
    assert impacts == ["Localised flooding", "Lightning damage"]
    assert clean_event("Yellow High Temperature") == "High Temperature"
    assert clean_event("Severe Rain") == "Rain"


def test_display_line_omits_area_when_title_already_contains_area():
    item = parse_rss(RSS)[2]
    cap = LAND_CAP.replace(
        "<headline>Orange Rain Warning</headline>",
        (
            "<headline>Thunderstorm warning for Cavan, Donegal, Monaghan, "
            "Connacht, Longford</headline>"
        ),
    ).replace(
        "<areaDesc>Ireland</areaDesc>",
        "<areaDesc>Cavan, Donegal, Monaghan, Connacht, Longford</areaDesc>",
    )
    warning = parse_cap(cap, item)

    assert warning.display_title == (
        "Thunderstorm warning for Cavan, Donegal, Monaghan, Connacht, Longford"
    )
    assert warning.area == "Cavan, Donegal, Monaghan, Connacht, Longford"
    assert warning.display_line == "Orange · 07 Jun 09:00 to 07 Jun 18:00"
