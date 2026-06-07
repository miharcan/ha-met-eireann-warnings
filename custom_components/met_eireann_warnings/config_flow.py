"""Config flow for Met Eireann Warnings."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_INCLUDE_ENVIRONMENTAL,
    CONF_INCLUDE_LAND,
    CONF_INCLUDE_MARINE,
    DEFAULT_INCLUDE_ENVIRONMENTAL,
    DEFAULT_INCLUDE_LAND,
    DEFAULT_INCLUDE_MARINE,
    DOMAIN,
)


class MetEireannWarningsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Met Eireann Warnings."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Met Eireann Warnings",
                data={},
                options=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_options_schema(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""

        return MetEireannWarningsOptionsFlow(config_entry)


class MetEireannWarningsOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Met Eireann Warnings."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""

        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self._config_entry.options)),
        )


def _options_schema(options: dict[str, Any] | None = None) -> vol.Schema:
    options = options or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_INCLUDE_LAND,
                default=options.get(CONF_INCLUDE_LAND, DEFAULT_INCLUDE_LAND),
            ): bool,
            vol.Required(
                CONF_INCLUDE_MARINE,
                default=options.get(CONF_INCLUDE_MARINE, DEFAULT_INCLUDE_MARINE),
            ): bool,
            vol.Required(
                CONF_INCLUDE_ENVIRONMENTAL,
                default=options.get(
                    CONF_INCLUDE_ENVIRONMENTAL, DEFAULT_INCLUDE_ENVIRONMENTAL
                ),
            ): bool,
        }
    )
