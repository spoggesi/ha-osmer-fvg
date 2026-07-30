"""Sensor platform for the OSMER FVG integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN
from .coordinator import OsmerDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class OsmerSensorEntityDescription(
    SensorEntityDescription,
):
    """Describe an OSMER sensor."""

    value_fn: Callable[
        [list],
        object,
    ]


SENSOR_DESCRIPTIONS = (
    OsmerSensorEntityDescription(
        key="station_count",
        name="Station count",
        value_fn=lambda data: len(data),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OSMER sensors."""

    coordinator: OsmerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            OsmerSensor(
                coordinator,
                description,
            )
            for description in SENSOR_DESCRIPTIONS
        ]
    )


class OsmerSensor(
    CoordinatorEntity[OsmerDataUpdateCoordinator],
    SensorEntity,
):
    """Representation of an OSMER sensor."""

    entity_description: OsmerSensorEntityDescription

    def __init__(
        self,
        coordinator: OsmerDataUpdateCoordinator,
        description: OsmerSensorEntityDescription,
    ) -> None:
        """Initialize sensor."""

        super().__init__(coordinator)

        self.entity_description = description

        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def native_value(self) -> object:
        """Return sensor value."""

        return self.entity_description.value_fn(self.coordinator.data)
