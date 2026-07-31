"""Test config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries

from custom_components.osmer_fvg.const import DOMAIN


async def test_user_flow(hass):
    """Test initial config flow step."""

    station = type(
        "Station",
        (),
        {
            "id": 51,
            "name": "Dignano",
            "latitude": 46.0,
            "longitude": 13.0,
            "altitude": 100,
        },
    )()

    with (
        patch(
            "custom_components.osmer_fvg.flow.service.FlowService.load_stations",
            new_callable=AsyncMock,
            return_value=[
                station,
            ],
        ),
        patch(
            "custom_components.osmer_fvg.flow.service.FlowService.preload",
            new_callable=AsyncMock,
        ),
        patch(
            "custom_components.osmer_fvg.flow.loader.FlowLoader.get_sensors",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_USER,
            },
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"