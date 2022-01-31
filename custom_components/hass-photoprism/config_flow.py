"""Config flow for Photoprism integration."""
import logging

import aiophotoprism
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import (CONF_NAME, CONF_PASSWORD, CONF_URL,
                                 CONF_USERNAME, CONF_VERIFY_SSL)

from .const import DEFAULT_NAME, DEFAULT_URL, DEFAULT_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect."""

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data[CONF_NAME] == data[CONF_NAME]:
            raise AlreadyConfigured

    # try:
    async with aiophotoprism.Photoprism(
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        url=data[CONF_URL],
        verify_ssl=data[CONF_VERIFY_SSL],
        loop=hass.loop,
    ) as client:
        await client.config()
        return {"title": f"{data[CONF_NAME]} ({data[CONF_URL]})"}
    # except aiophotoprism.exceptions.PhotoprismUnauthorizedError as error:
    #     raise InvalidAuth from error
    # except Exception as error:
    #     raise CannotConnect from error


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for photoprism."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors[CONF_USERNAME] = "invalid_auth"
                errors[CONF_PASSWORD] = "invalid_auth"
            except AlreadyConfigured:
                errors[CONF_NAME] = "already_configured"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class AlreadyConfigured(exceptions.HomeAssistantError):
    """Error to indicate device is already configured."""
