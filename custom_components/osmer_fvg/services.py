"""Services for OSMER FVG integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN
from .logging import set_request_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(
    hass: HomeAssistant,
) -> None:
    """Set up OSMER FVG services."""

    async def handle_test_notification(call: ServiceCall) -> None:
        """Handle test notification service call."""
        request_id = set_request_id()
        message = call.data.get("message", "Test notification from OSMER FVG")

        _LOGGER.info(
            "Sending test notification",
            message=message,
            request_id=request_id,
        )

        await hass.services.async_call(
            "notify",
            "notify",
            {
                "title": "OSMER FVG Test",
                "message": message,
                "data": {"tag": DOMAIN, "priority": "high"},
            },
        )

    # Register test notification service (without await)
    if not hass.services.has_service(DOMAIN, "test_notification"):
        async_register_admin_service(
            hass,
            DOMAIN,
            "test_notification",
            handle_test_notification,
        )
