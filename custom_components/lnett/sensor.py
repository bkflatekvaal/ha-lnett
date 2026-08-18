"""Sensors for Lnett Tariff."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, NAME, SOURCE_URL
from .coordinator import LnettDataUpdateCoordinator
from .parser import TariffData
from .tariff_period import is_day_tariff


@dataclass(frozen=True, kw_only=True)
class LnettSensorDescription(SensorEntityDescription):
    value_fn: Callable[[TariffData], float]


SENSORS = (
    LnettSensorDescription(
        key="energy_day",
        translation_key="energy_day",
        native_unit_of_measurement="øre/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: d.energy_day,
    ),
    LnettSensorDescription(
        key="energy_night_weekend",
        translation_key="energy_night_weekend",
        native_unit_of_measurement="øre/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
        value_fn=lambda d: d.energy_night_weekend,
    ),
    LnettSensorDescription(
        key="consumption_tax",
        translation_key="consumption_tax",
        native_unit_of_measurement="øre/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:bank",
        value_fn=lambda d: d.consumption_tax,
    ),
    LnettSensorDescription(
        key="enova_fee",
        translation_key="enova_fee",
        native_unit_of_measurement="øre/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:leaf",
        value_fn=lambda d: d.enova_fee,
    ),
    *tuple(
        LnettSensorDescription(
            key=f"capacity_{low}_{high}",
            translation_key=f"capacity_{low}_{high}",
            native_unit_of_measurement="NOK/mnd",
            state_class=SensorStateClass.MEASUREMENT,
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
    entities = [
        LnettTariffSensor(coordinator, entry, description) for description in SENSORS
    ]
    entities.append(LnettCurrentEnergyPriceSensor(coordinator, entry))
    async_add_entities(entities)


class _LnettBaseSensor(CoordinatorEntity[LnettDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="Lnett",
            model="Public tariff",
            configuration_url=SOURCE_URL,
        )

    @property
    def extra_state_attributes(self):
        return {
            "valid_from": self.coordinator.data.valid_from.isoformat(),
            "source": SOURCE_URL,
        }


class LnettTariffSensor(_LnettBaseSensor):
    entity_description: LnettSensorDescription

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)


class LnettCurrentEnergyPriceSensor(_LnettBaseSensor):
    """Current energy tariff, automatically switching between day and night/weekend."""

    _attr_translation_key = "energy_price"
    _attr_native_unit_of_measurement = "øre/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash-clock"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_energy_price"
        self._remove_time_listener = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._remove_time_listener = async_track_time_interval(
            self.hass, self._async_time_changed, timedelta(minutes=1)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_time_listener is not None:
            self._remove_time_listener()
            self._remove_time_listener = None
        await super().async_will_remove_from_hass()

    @callback
    def _async_time_changed(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self):
        if is_day_tariff(dt_util.now()):
            return self.coordinator.data.energy_day
        return self.coordinator.data.energy_night_weekend

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        day = is_day_tariff(dt_util.now())
        attrs.update({
            "Day": self.coordinator.data.energy_day,
            "Night": self.coordinator.data.energy_night_weekend,
            "tariff_period": "day" if day else "night_weekend",
            "day_tariff": day,
        })
        return attrs


class LnettTotalSensor(_LnettBaseSensor):
    """Current total variable grid cost per kWh."""

    _attr_translation_key = "total"
    _attr_native_unit_of_measurement = "øre/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total"
        self._remove_time_listener = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._remove_time_listener = async_track_time_interval(
            self.hass, self._async_time_changed, timedelta(minutes=1)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_time_listener is not None:
            self._remove_time_listener()
            self._remove_time_listener = None
        await super().async_will_remove_from_hass()

    @callback
    def _async_time_changed(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self):
        data = self.coordinator.data
        energy = data.energy_day if is_day_tariff(dt_util.now()) else data.energy_night_weekend
        return round(energy + data.consumption_tax + data.enova_fee, 2)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        attrs = super().extra_state_attributes
        current_energy = data.energy_day if is_day_tariff(dt_util.now()) else data.energy_night_weekend
        attrs.update({
            "Energy tariff": current_energy,
            "Consumption tax": data.consumption_tax,
            "Enova fee": data.enova_fee,
            "Day total": round(data.energy_day + data.consumption_tax + data.enova_fee, 2),
            "Night total": round(data.energy_night_weekend + data.consumption_tax + data.enova_fee, 2),
        })
        return attrs
