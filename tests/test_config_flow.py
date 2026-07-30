"""Test config flow."""

from homeassistant import config_entries


async def test_user_flow(hass):
    """Test user config flow."""

    result = await hass.config_entries.flow.async_init(
        "osmer_fvg",
        context={
            "source": config_entries.SOURCE_USER,
        },
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
