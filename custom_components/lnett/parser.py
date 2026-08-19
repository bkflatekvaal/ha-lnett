"""Defensive parser for Lnett's public private-customer tariff page."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
import re


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    @property
    def text(self) -> str:
        return " ".join(self.parts)


@dataclass(frozen=True)
class TariffData:
    valid_from: date
    capacity: dict[str, float]
    energy_day: float
    energy_night_weekend: float
    consumption_tax: float
    enova_fee: float


def _number(value: str) -> float:
    return float(value.replace("\xa0", "").replace(" ", "").replace(",", "."))


def _find_number(text: str, label_pattern: str, unit_pattern: str) -> float:
    pattern = rf"{label_pattern}\s+([0-9][0-9\s.,]*)\s*{unit_pattern}"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not find tariff value for {label_pattern}")
    return _number(match.group(1))


def _find_capacity_tariffs(text: str) -> dict[str, float]:
    """Return every capacity tariff published in the price table."""
    pattern = re.compile(
        r"Kapasitetsledd\s*"
        r"([0-9]+(?:[.,][0-9]+)?)\s*[-‐‑‒–—]\s*"
        r"([0-9]+(?:[.,][0-9]+)?)\s*kW\s+"
        r"([0-9][0-9\s.,]*)\s*kr\s*/?\s*mnd",
        flags=re.IGNORECASE,
    )
    capacity: dict[str, float] = {}
    for match in pattern.finditer(text):
        low = _number(match.group(1))
        high = _number(match.group(2))
        if low >= high:
            raise ValueError(f"Invalid capacity tariff range: {low:g}-{high:g}")
        capacity.setdefault(f"{low:g}-{high:g}", _number(match.group(3)))

    if not capacity:
        raise ValueError("Could not find any capacity tariffs")
    return capacity


def parse_tariffs(html: str) -> TariffData:
    extractor = _TextExtractor()
    extractor.feed(html)
    text = re.sub(r"\s+", " ", extractor.text)

    date_match = re.search(
        r"Prisliste,\s*pr\s*(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE
    )
    if not date_match:
        raise ValueError("Could not find tariff validity date")
    valid_from = date(
        int(date_match.group(3)), int(date_match.group(2)), int(date_match.group(1))
    )

    data = TariffData(
        valid_from=valid_from,
        capacity=_find_capacity_tariffs(text),
        energy_day=_find_number(text, r"Energiledd,\s*dag", r"øre\s*/?\s*kWh"),
        energy_night_weekend=_find_number(
            text, r"Energiledd,\s*natt\s*/\s*helg", r"øre\s*/?\s*kWh"
        ),
        consumption_tax=_find_number(text, r"Forbruksavgift", r"øre\s*/?\s*kWh"),
        enova_fee=_find_number(
            text, r"Enovaavgift\s*/\s*Energifondet", r"øre\s*/?\s*kWh"
        ),
    )
    _validate(data)
    return data


def _validate(data: TariffData) -> None:
    if not (0 < data.energy_day < 300):
        raise ValueError("Energy day price outside expected range")
    if not (0 < data.energy_night_weekend < 300):
        raise ValueError("Energy night/weekend price outside expected range")
    if not (0 < data.consumption_tax < 100):
        raise ValueError("Consumption tax outside expected range")
    if not (0 < data.enova_fee < 100):
        raise ValueError("Enova fee outside expected range")
    if any(not (0 < value < 10000) for value in data.capacity.values()):
        raise ValueError("Capacity price outside expected range")
