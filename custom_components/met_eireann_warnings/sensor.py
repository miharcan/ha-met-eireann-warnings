"""Sensor platform for Met Eireann Warnings."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, ATTRIBUTION_DETAIL, DOMAIN, MET_EIREANN_WARNINGS_URL
from .coordinator import MetEireannWarningsCoordinator, WarningsData

MAX_STATE_LENGTH = 255


@dataclass(frozen=True, kw_only=True)
class MetEireannWarningsSensorEntityDescription(SensorEntityDescription):
    """Description of a Met Eireann Warnings sensor."""

    value_fn: Callable[[WarningsData], Any]
    attributes_fn: Callable[[WarningsData], dict[str, Any]] | None = None


SENSORS: tuple[MetEireannWarningsSensorEntityDescription, ...] = (
    MetEireannWarningsSensorEntityDescription(
        key="warnings",
        name="Warnings",
        value_fn=lambda data: data.counts["total"],
        attributes_fn=lambda data: {
            "warnings": [warning.as_dict() for warning in data.warnings],
            "warning_count": data.counts["total"],
            "land_warning_count": data.counts["land"],
            "marine_warning_count": data.counts["marine"],
            "environmental_warning_count": data.counts["environmental"],
            "highest_level": data.highest_level,
            "summary_state": data.summary_state,
            "summary_source": data.summary_source,
            "attribution_detail": ATTRIBUTION_DETAIL,
            "source_url": MET_EIREANN_WARNINGS_URL,
        },
    ),
    MetEireannWarningsSensorEntityDescription(
        key="warning_count",
        name="Warning Count",
        value_fn=lambda data: data.counts["total"],
    ),
    MetEireannWarningsSensorEntityDescription(
        key="land_warning_count",
        name="Land Warning Count",
        value_fn=lambda data: data.counts["land"],
    ),
    MetEireannWarningsSensorEntityDescription(
        key="marine_warning_count",
        name="Marine Warning Count",
        value_fn=lambda data: data.counts["marine"],
    ),
    MetEireannWarningsSensorEntityDescription(
        key="environmental_warning_count",
        name="Environmental Warning Count",
        value_fn=lambda data: data.counts["environmental"],
    ),
    MetEireannWarningsSensorEntityDescription(
        key="highest_warning_level",
        name="Highest Warning Level",
        value_fn=lambda data: data.highest_level,
    ),
    MetEireannWarningsSensorEntityDescription(
        key="summary_source",
        name="Warnings Summary Source",
        value_fn=lambda data: _state_safe_text(data.summary_state),
        attributes_fn=lambda data: {
            "summary_state": data.summary_state,
            "summary_source": data.summary_source,
            "attribution_detail": ATTRIBUTION_DETAIL,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Met Eireann Warnings sensors."""

    coordinator: MetEireannWarningsCoordinator = entry.runtime_data
    async_add_entities(
        MetEireannWarningsSensor(coordinator, entry, description)
        for description in SENSORS
    )


class MetEireannWarningsSensor(
    CoordinatorEntity[MetEireannWarningsCoordinator], SensorEntity
):
    """Met Eireann Warnings sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MetEireannWarningsCoordinator,
        entry: ConfigEntry,
        description: MetEireannWarningsSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""

        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_name = description.name
        self._attr_entity_category = description.entity_category
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Met Eireann Warnings",
            "manufacturer": "Met Eireann",
            "configuration_url": MET_EIREANN_WARNINGS_URL,
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""

        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""

        attributes = {
            "attribution": ATTRIBUTION,
            "source": "Met Eireann",
            "source_url": MET_EIREANN_WARNINGS_URL,
        }
        if self.entity_description.attributes_fn is not None:
            attributes.update(self.entity_description.attributes_fn(self.coordinator.data))
        return attributes


def _state_safe_text(value: str) -> str:
    """Return text that fits inside Home Assistant's sensor state limit."""

    if len(value) <= MAX_STATE_LENGTH:
        return value
    return f"{value[: MAX_STATE_LENGTH - 3].rstrip()}..."
