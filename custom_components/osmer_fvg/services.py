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
    
    # Register test notification service
    await async_register_admin_service(
        hass,
        DOMAIN,
        "test_notification",
        handle_test_notification,
    )

    async def handle_alert_notification(call: ServiceCall) -> None:
        """Handle alert notification service call."""
        request_id = set_request_id()
        title = call.data.get("title", "OSMER FVG Alert")
        message = call.data.get("message", "")
        level = call.data.get("level", "info")
        zones = call.data.get("zones", [])
        
        _LOGGER.info(
            "Sending alert notification",
            title=title,
            level=level,
            zones=zones,
            request_id=request_id,
        )
        
        # Determine emoji based on level
        level_emoji = {
            "green": "✅",
            "yellow": "⚠️",
            "orange": "🟠",
            "red": "🔴",
        }.get(level, "🔵")
        
        full_title = f"{level_emoji} {title}"
        full_message = f"{message}\n\nLivello: {level.upper()}\nZones: {', '.join(zones) if zones else 'Tutte'}"
        
        await hass.services.async_call(
            "notify",
            "notify",
            {
                "title": full_title,
                "message": full_message,
                "data": {
                    "tag": DOMAIN,
                    "priority": "high" if level in ["orange", "red"] else "normal",
                    "level": level,
                },
            },
        )
    
    # Register alert notification service
    await async_register_admin_service(
        hass,
        DOMAIN,
        "alert_notification",
        handle_alert_notification,
    )
