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

    capacity = {}
    for low, high in ((0, 2), (2, 5), (5, 10), (10, 15), (15, 20), (20, 25)):
        key = f"{low}-{high}"
        capacity[key] = _find_number(
            text,
            rf"Kapasitetsledd\s*{low}\s*-\s*{high}\s*kW",
            r"kr\s*/?\s*mnd",
        )

    data = TariffData(
        valid_from=valid_from,
        capacity=capacity,
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
    if set(data.capacity) != {"0-2", "2-5", "5-10", "10-15", "15-20", "20-25"}:
        raise ValueError("Incomplete capacity tariff table")
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
