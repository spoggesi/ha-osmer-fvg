"""Test config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries

from custom_components.osmer_fvg.const import DOMAIN


async def test_user_flow(hass):
    """Test user config flow."""

    with patch(
        "custom_components.osmer_fvg.config_flow.OsmerApiClient.get_stations",
        new_callable=AsyncMock,
        return_value=[
            type(
                "Station",
                (),
                {
                    "id": 51,
                    "name": "Dignano",
                },
            )()
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_USER,
            },
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"