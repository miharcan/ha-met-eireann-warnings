"""Data coordinator for Met Eireann Warnings."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import xml.etree.ElementTree as ET

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CATEGORY_ENVIRONMENTAL,
    CATEGORY_LAND,
    CATEGORY_MARINE,
    CONF_INCLUDE_ENVIRONMENTAL,
    CONF_INCLUDE_LAND,
    CONF_INCLUDE_MARINE,
    DEFAULT_INCLUDE_ENVIRONMENTAL,
    DEFAULT_INCLUDE_LAND,
    DEFAULT_INCLUDE_MARINE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RSS_URL,
)
from .parser import (
    Warning,
    build_summary_source,
    build_summary_state,
    deduplicate_warnings,
    highest_level,
    parse_cap,
    parse_rss,
    warning_counts,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class WarningsData:
    """Current warnings data."""

    warnings: list[Warning]
    counts: dict[str, int]
    highest_level: str
    summary_state: str
    summary_source: str


class MetEireannWarningsCoordinator(DataUpdateCoordinator[WarningsData]):
    """Coordinator that fetches the RSS feed and linked CAP XML warnings."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> WarningsData:
        try:
            feed_xml = await self._fetch_text(RSS_URL)
            feed_items = parse_rss(feed_xml)
            warnings = await self._fetch_cap_warnings(feed_items)
        except (
            ClientError,
            TimeoutError,
            asyncio.TimeoutError,
            ValueError,
            ET.ParseError,
        ) as err:
            raise UpdateFailed(f"Failed to update Met Eireann warnings: {err}") from err

        warnings = deduplicate_warnings(warnings)
        warnings = self._filter_warnings(warnings)

        return WarningsData(
            warnings=warnings,
            counts=warning_counts(warnings),
            highest_level=highest_level(warnings),
            summary_state=build_summary_state(warnings),
            summary_source=build_summary_source(warnings),
        )

    async def _fetch_cap_warnings(self, feed_items) -> list[Warning]:
        tasks = [self._fetch_one_cap(item) for item in feed_items if item.link]
        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        warnings: list[Warning] = []
        for result in results:
            if isinstance(result, Warning):
                warnings.append(result)
            else:
                _LOGGER.warning("Skipping Met Eireann CAP warning: %s", result)
        return warnings

    async def _fetch_one_cap(self, feed_item) -> Warning:
        cap_xml = await self._fetch_text(feed_item.link)
        return parse_cap(cap_xml, feed_item)

    async def _fetch_text(self, url: str) -> str:
        async with asyncio.timeout(20):
            async with self._session.get(url) as response:
                response.raise_for_status()
                return await response.text()

    def _filter_warnings(self, warnings: list[Warning]) -> list[Warning]:
        options = self.config_entry.options
        include_land = options.get(CONF_INCLUDE_LAND, DEFAULT_INCLUDE_LAND)
        include_marine = options.get(CONF_INCLUDE_MARINE, DEFAULT_INCLUDE_MARINE)
        include_environmental = options.get(
            CONF_INCLUDE_ENVIRONMENTAL, DEFAULT_INCLUDE_ENVIRONMENTAL
        )

        return [
            warning
            for warning in warnings
            if (
                (warning.category == CATEGORY_LAND and include_land)
                or (warning.category == CATEGORY_MARINE and include_marine)
                or (
                    warning.category == CATEGORY_ENVIRONMENTAL
                    and include_environmental
                )
            )
        ]
