"""Constants for the Met Eireann Warnings integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "met_eireann_warnings"

ATTRIBUTION = "Data provided by Met Eireann"
ATTRIBUTION_DETAIL = (
    "Weather warning headline and description text is provided by Met Eireann "
    "and is exposed unchanged."
)

RSS_URL = "https://www.met.ie/warningsxml/rss.xml"
MET_EIREANN_WARNINGS_URL = "https://www.met.ie/warnings"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

CONF_INCLUDE_LAND = "include_land"
CONF_INCLUDE_MARINE = "include_marine"
CONF_INCLUDE_ENVIRONMENTAL = "include_environmental"

DEFAULT_INCLUDE_LAND = True
DEFAULT_INCLUDE_MARINE = True
DEFAULT_INCLUDE_ENVIRONMENTAL = True

CATEGORY_LAND = "Land"
CATEGORY_MARINE = "Marine"
CATEGORY_ENVIRONMENTAL = "Environmental"

LEVEL_NONE = "none"
LEVEL_YELLOW = "yellow"
LEVEL_ORANGE = "orange"
LEVEL_RED = "red"

LEVEL_RANK = {
    LEVEL_NONE: 0,
    LEVEL_YELLOW: 1,
    LEVEL_ORANGE: 2,
    LEVEL_RED: 3,
}

SEVERITY_TO_LEVEL = {
    "minor": LEVEL_NONE,
    "moderate": LEVEL_YELLOW,
    "severe": LEVEL_ORANGE,
    "extreme": LEVEL_RED,
}
