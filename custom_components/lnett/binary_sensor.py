"""Binary sensors for Lnett Tariff."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, NAME, SOURCE_URL
from .coordinator import LnettDataUpdateCoordinator
from .tariff_period import is_day_tariff


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LnettDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LnettDayTariffBinarySensor(coordinator, entry)])


class LnettDayTariffBinarySensor(
    CoordinatorEntity[LnettDataUpdateCoordinator], BinarySensorEntity
):
    """ON when Lnett day tariff applies, OFF otherwise."""

    _attr_has_entity_name = True
    _attr_translation_key = "day_tariff"
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_day_tariff"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="Lnett",
            model="Public tariff",
            configuration_url=SOURCE_URL,
        )
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
    def is_on(self) -> bool:
        return is_day_tariff(dt_util.now())

    @property
    def extra_state_attributes(self):
        return {
            "period": "day" if self.is_on else "night_weekend",
            "source": SOURCE_URL,
        }
