from datetime import datetime
import importlib.util
from pathlib import Path

MODULE = Path(__file__).parents[1] / "custom_components" / "lnett" / "tariff_period.py"
spec = importlib.util.spec_from_file_location("tariff_period", MODULE)
tariff_period = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tariff_period)


def test_weekday_day():
    assert tariff_period.is_day_tariff(datetime(2026, 8, 18, 12, 0)) is True


def test_weekday_night():
    assert tariff_period.is_day_tariff(datetime(2026, 8, 18, 5, 59)) is False
    assert tariff_period.is_day_tariff(datetime(2026, 8, 18, 22, 0)) is False


def test_weekend():
    assert tariff_period.is_day_tariff(datetime(2026, 8, 22, 12, 0)) is False


def test_public_holiday():
    # Constitution Day 2027 is a Monday.
    assert tariff_period.is_day_tariff(datetime(2027, 5, 17, 12, 0)) is False
    # Ascension Day 2026
    assert tariff_period.is_day_tariff(datetime(2026, 5, 14, 12, 0)) is False
