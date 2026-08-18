"""Sensors for Lnett Tariff."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, SOURCE_URL
from .coordinator import LnettDataUpdateCoordinator
from .parser import TariffData


@dataclass(frozen=True, kw_only=True)
class LnettSensorDescription(SensorEntityDescription):
    value_fn: Callable[[TariffData], float]


SENSORS = (
    LnettSensorDescription(
        key="energy_day",
        translation_key="energy_day",
        native_unit_of_measurement="øre/kWh",
        icon="mdi:weather-sunny",
        value_fn=lambda d: d.energy_day,
    ),
    LnettSensorDescription(
        key="energy_night_weekend",
        translation_key="energy_night_weekend",
        native_unit_of_measurement="øre/kWh",
        icon="mdi:weather-night",
        value_fn=lambda d: d.energy_night_weekend,
    ),
    LnettSensorDescription(
        key="consumption_tax",
        translation_key="consumption_tax",
        native_unit_of_measurement="øre/kWh",
        icon="mdi:bank",
        value_fn=lambda d: d.consumption_tax,
    ),
    LnettSensorDescription(
        key="enova_fee",
        translation_key="enova_fee",
        native_unit_of_measurement="øre/kWh",
        icon="mdi:leaf",
        value_fn=lambda d: d.enova_fee,
    ),
    *tuple(
        LnettSensorDescription(
            key=f"capacity_{low}_{high}",
            translation_key=f"capacity_{low}_{high}",
            native_unit_of_measurement="NOK/mnd",
            icon="mdi:transmission-tower",
            value_fn=lambda d, key=f"{low}-{high}": d.capacity[key],
        )
        for low, high in ((0, 2), (2, 5), (5, 10), (10, 15), (15, 20), (20, 25))
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LnettDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LnettTariffSensor(coordinator, entry, description) for description in SENSORS
    )


class LnettTariffSensor(CoordinatorEntity[LnettDataUpdateCoordinator], SensorEntity):
    entity_description: LnettSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="Lnett",
            model="Public tariff",
            configuration_url=SOURCE_URL,
        )

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        return {
            "valid_from": self.coordinator.data.valid_from.isoformat(),
            "source": SOURCE_URL,
        }
