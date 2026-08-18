"""Data coordinator for Lnett Tariff."""
from __future__ import annotations

from datetime import timedelta
import logging

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL_HOURS, DOMAIN, SOURCE_URL
from .parser import TariffData, parse_tariffs

_LOGGER = logging.getLogger(__name__)


class LnettDataUpdateCoordinator(DataUpdateCoordinator[TariffData]):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> TariffData:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                SOURCE_URL,
                timeout=30,
                headers={"User-Agent": "Home Assistant Lnett Tariff integration"},
            ) as response:
                response.raise_for_status()
                html = await response.text()
            return parse_tariffs(html)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Unable to update Lnett tariff data: {err}") from err
