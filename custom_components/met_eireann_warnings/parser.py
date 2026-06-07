"""Parsing helpers for Met Eireann RSS and CAP warning feeds."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from .const import (
    CATEGORY_ENVIRONMENTAL,
    CATEGORY_LAND,
    CATEGORY_MARINE,
    LEVEL_NONE,
    LEVEL_ORANGE,
    LEVEL_RANK,
    LEVEL_RED,
    LEVEL_YELLOW,
    SEVERITY_TO_LEVEL,
)

CAP_NS = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}


@dataclass(slots=True)
class FeedItem:
    """Warning item found in the RSS feed."""

    title: str
    link: str
    description: str
    category: str
    guid: str
    published: str | None


@dataclass(slots=True)
class Warning:
    """Structured warning parsed from RSS and CAP XML."""

    identifier: str
    title: str
    category: str
    event: str | None
    level: str
    severity: str | None
    urgency: str | None
    certainty: str | None
    sent: str | None
    effective: str | None
    onset: str | None
    expires: str | None
    published: str | None
    headline: str
    description: str
    instruction: str | None
    area: str | None
    geocodes: list[str]
    link: str
    web: str | None
    source: str = "Met Eireann"
    duplicate_count: int = 0
    duplicate_identifiers: list[str] = field(default_factory=list)
    duplicate_links: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a Home Assistant attribute-friendly dictionary."""

        return asdict(self)


def parse_rss(feed_xml: str) -> list[FeedItem]:
    """Parse Met Eireann RSS XML into feed items."""

    root = ET.fromstring(feed_xml)
    items: list[FeedItem] = []

    for item in root.findall("./channel/item"):
        items.append(
            FeedItem(
                title=_text(item, "title") or "",
                link=normalize_url(_text(item, "link") or ""),
                description=_text(item, "description") or "",
                category=classify_category(_text(item, "category") or ""),
                guid=normalize_url(_text(item, "guid") or ""),
                published=_parse_rss_date(_text(item, "pubDate")),
            )
        )

    return items


def parse_cap(cap_xml: str, feed_item: FeedItem) -> Warning:
    """Parse a CAP XML warning, falling back to RSS fields where needed."""

    root = ET.fromstring(cap_xml)
    info = root.find("cap:info", CAP_NS)

    identifier = _cap_text(root, "identifier") or feed_item.guid or feed_item.link
    severity = _cap_text(info, "severity")
    level = _level_from_cap(info, severity)
    headline = _cap_text(info, "headline") or feed_item.title
    description = _cap_text(info, "description") or feed_item.description
    area = _first_area_desc(info)
    geocodes = _geocodes(info)
    web = _cap_text(info, "web")
    event = _cap_text(info, "event")

    return Warning(
        identifier=identifier,
        title=feed_item.title or headline,
        category=classify_category(feed_item.category, event=event, geocodes=geocodes),
        event=event,
        level=level,
        severity=severity,
        urgency=_cap_text(info, "urgency"),
        certainty=_cap_text(info, "certainty"),
        sent=_cap_text(root, "sent"),
        effective=_cap_text(info, "effective"),
        onset=_cap_text(info, "onset"),
        expires=_cap_text(info, "expires"),
        published=feed_item.published,
        headline=headline,
        description=description,
        instruction=_cap_text(info, "instruction"),
        area=area,
        geocodes=geocodes,
        link=feed_item.link,
        web=web,
    )


def classify_category(
    category: str | None,
    *,
    event: str | None = None,
    geocodes: list[str] | None = None,
) -> str:
    """Normalize feed categories into the integration's public categories."""

    category_text = (category or "").strip().lower()
    event_text = (event or "").strip().lower()
    geocodes = geocodes or []

    if category_text == "marine" or event_text in {"small craft", "gale"}:
        return CATEGORY_MARINE
    if category_text == "environmental" or "blight" in event_text:
        return CATEGORY_ENVIRONMENTAL
    if any(code.startswith("EI8") for code in geocodes):
        return CATEGORY_MARINE
    return CATEGORY_LAND


def deduplicate_warnings(warnings: list[Warning]) -> list[Warning]:
    """Remove duplicate and near-duplicate warnings while preserving metadata."""

    deduped_by_exact: dict[str, Warning] = {}
    for warning in warnings:
        exact_key = _exact_key(warning)
        existing = deduped_by_exact.get(exact_key)
        if existing is None:
            deduped_by_exact[exact_key] = warning
            continue
        _merge_duplicate(existing, warning)

    deduped_by_content: dict[tuple[str, ...], Warning] = {}
    for warning in deduped_by_exact.values():
        content_key = _content_key(warning)
        existing = deduped_by_content.get(content_key)
        if existing is None:
            deduped_by_content[content_key] = warning
            continue
        _merge_duplicate(existing, warning)

    return sorted(
        deduped_by_content.values(),
        key=lambda warning: (
            -LEVEL_RANK.get(warning.level, 0),
            warning.expires or "",
            warning.headline.lower(),
        ),
    )


def warning_counts(warnings: list[Warning]) -> dict[str, int]:
    """Return warning counts by normalized category."""

    return {
        "total": len(warnings),
        "land": sum(1 for warning in warnings if warning.category == CATEGORY_LAND),
        "marine": sum(1 for warning in warnings if warning.category == CATEGORY_MARINE),
        "environmental": sum(
            1 for warning in warnings if warning.category == CATEGORY_ENVIRONMENTAL
        ),
    }


def highest_level(warnings: list[Warning]) -> str:
    """Return the highest active warning level."""

    level = LEVEL_NONE
    for warning in warnings:
        if LEVEL_RANK.get(warning.level, 0) > LEVEL_RANK[level]:
            level = warning.level
    return level


def build_summary_source(warnings: list[Warning]) -> str:
    """Build structured factual text for HA-side AI summarisation."""

    if not warnings:
        return (
            "Met Eireann warnings\n"
            "Status: No active warnings in the feed.\n"
            "Attribution: Data provided by Met Eireann."
        )

    counts = warning_counts(warnings)
    level = highest_level(warnings)
    lines = [
        "Met Eireann warnings",
        f"Status: {counts['total']} active warning{_plural(counts['total'])}.",
        f"Highest level: {level}.",
        (
            "Breakdown: "
            f"{counts['land']} land, "
            f"{counts['marine']} marine, "
            f"{counts['environmental']} environmental."
        ),
    ]

    for category in (CATEGORY_LAND, CATEGORY_MARINE, CATEGORY_ENVIRONMENTAL):
        category_warnings = [
            warning for warning in warnings if warning.category == category
        ]
        if not category_warnings:
            continue
        lines.append("")
        lines.append(f"{category}:")
        for warning in category_warnings:
            lines.extend(_summary_lines_for_warning(warning))

    lines.append("")
    lines.append(
        "Attribution: Data provided by Met Eireann. Original warning headline "
        "and description fields are exposed unchanged in warning attributes."
    )

    return "\n".join(lines)


def build_summary_state(warnings: list[Warning]) -> str:
    """Build a compact sensor-state summary."""

    if not warnings:
        return "No active Met Eireann warnings."

    counts = warning_counts(warnings)
    parts = [f"{counts['total']} active warning{_plural(counts['total'])}"]
    category_parts = []
    if counts["land"]:
        category_parts.append(f"{counts['land']} land")
    if counts["marine"]:
        category_parts.append(f"{counts['marine']} marine")
    if counts["environmental"]:
        category_parts.append(f"{counts['environmental']} environmental")
    if category_parts:
        parts.append(", ".join(category_parts))
    parts.append(f"highest {highest_level(warnings)}")

    return "Met Eireann: " + "; ".join(parts) + "."


def normalize_url(url: str) -> str:
    """Normalize warning URLs so exact duplicate links compare cleanly."""

    if not url:
        return ""
    split = urlsplit(url.strip())
    path = re.sub(r"/{2,}", "/", split.path)
    return urlunsplit((split.scheme.lower(), split.netloc.lower(), path, "", ""))


def _text(element: ET.Element, tag: str) -> str | None:
    child = element.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _cap_text(element: ET.Element | None, tag: str) -> str | None:
    if element is None:
        return None
    child = element.find(f"cap:{tag}", CAP_NS)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _first_area_desc(info: ET.Element | None) -> str | None:
    if info is None:
        return None
    area = info.find("cap:area", CAP_NS)
    return _cap_text(area, "areaDesc")


def _geocodes(info: ET.Element | None) -> list[str]:
    if info is None:
        return []
    values = []
    for geocode in info.findall(".//cap:geocode", CAP_NS):
        value = _cap_text(geocode, "value")
        if value:
            values.append(value)
    return values


def _level_from_cap(info: ET.Element | None, severity: str | None) -> str:
    awareness_level = None
    if info is not None:
        for parameter in info.findall("cap:parameter", CAP_NS):
            if _cap_text(parameter, "valueName") == "awareness_level":
                awareness_level = _cap_text(parameter, "value")
                break

    level_text = (awareness_level or "").lower()
    if LEVEL_RED in level_text:
        return LEVEL_RED
    if LEVEL_ORANGE in level_text:
        return LEVEL_ORANGE
    if LEVEL_YELLOW in level_text:
        return LEVEL_YELLOW
    return SEVERITY_TO_LEVEL.get((severity or "").lower(), LEVEL_NONE)


def _parse_rss_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return value


def _exact_key(warning: Warning) -> str:
    return warning.identifier or warning.link


def _content_key(warning: Warning) -> tuple[str, ...]:
    return (
        warning.category,
        warning.event or "",
        warning.level,
        _norm_text(warning.headline),
        _norm_text(warning.description),
        _norm_text(warning.area or ""),
        _minute(warning.onset),
        _minute(warning.expires),
    )


def _merge_duplicate(existing: Warning, duplicate: Warning) -> None:
    existing.duplicate_count += 1 + duplicate.duplicate_count
    if duplicate.identifier and duplicate.identifier != existing.identifier:
        existing.duplicate_identifiers.append(duplicate.identifier)
    for identifier in duplicate.duplicate_identifiers:
        if identifier not in existing.duplicate_identifiers:
            existing.duplicate_identifiers.append(identifier)
    if duplicate.link and duplicate.link != existing.link:
        existing.duplicate_links.append(duplicate.link)
    for link in duplicate.duplicate_links:
        if link not in existing.duplicate_links:
            existing.duplicate_links.append(link)

    if _date_sort_value(duplicate.sent or duplicate.published) > _date_sort_value(
        existing.sent or existing.published
    ):
        existing.sent = duplicate.sent
        existing.published = duplicate.published
        existing.link = duplicate.link


def _norm_text(value: str) -> str:
    return re.sub(r"\W+", " ", value.casefold()).strip()


def _minute(value: str | None) -> str:
    if not value:
        return ""
    return value[:16]


def _date_sort_value(value: str | None) -> float:
    if not value:
        return 0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0


def _summary_lines_for_warning(warning: Warning) -> list[str]:
    event = warning.event or "Warning"
    area = _readable_area(warning.area)
    timing = _readable_timing(warning)
    duplicate_note = (
        f" Duplicate RSS/CAP items collapsed: {warning.duplicate_count}."
        if warning.duplicate_count
        else ""
    )

    line = f"- {warning.level.title()} {event}"
    if area:
        line += f" - {area}"
    if timing:
        line += f" - {timing}"
    line += f".{duplicate_note}"

    lines = [line]
    if warning.description:
        lines.append(f"  Detail: {warning.description}")
    return lines


def _readable_area(area: str | None) -> str:
    if not area:
        return ""
    return re.sub(r"\s+", " ", area).strip()


def _readable_timing(warning: Warning) -> str:
    onset = _format_time(warning.onset)
    expires = _format_time(warning.expires)
    if onset and expires:
        return f"from {onset} until {expires}"
    if expires:
        return f"until {expires}"
    if onset:
        return f"from {onset}"
    return ""


def _format_time(value: str | None) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value).strftime("%d %b %H:%M")
    except ValueError:
        return value


def _plural(count: int) -> str:
    return "" if count == 1 else "s"
