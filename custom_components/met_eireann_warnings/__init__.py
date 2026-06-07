"""Met Eireann Warnings integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MetEireannWarningsCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MetEireannWarningsConfigEntry = ConfigEntry[MetEireannWarningsCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MetEireannWarningsConfigEntry,
) -> bool:
    """Set up Met Eireann Warnings from a config entry."""

    coordinator = MetEireannWarningsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MetEireannWarningsConfigEntry,
) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant,
    entry: MetEireannWarningsConfigEntry,
) -> None:
    """Reload the integration when options change."""

    await hass.config_entries.async_reload(entry.entry_id)
