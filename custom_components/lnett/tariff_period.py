"""Determine whether Lnett day tariff is active."""
from __future__ import annotations

from datetime import date, datetime, timedelta


def _easter_sunday(year: int) -> date:
    """Return Gregorian Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def norwegian_public_holidays(year: int) -> set[date]:
    """Return Norwegian public holidays relevant to Lnett tariff selection."""
    easter = _easter_sunday(year)
    return {
        date(year, 1, 1),            # New Year's Day
        easter - timedelta(days=3),  # Maundy Thursday
        easter - timedelta(days=2),  # Good Friday
        easter,                      # Easter Sunday
        easter + timedelta(days=1),  # Easter Monday
        date(year, 5, 1),            # Labour Day
        date(year, 5, 17),           # Constitution Day
        easter + timedelta(days=39), # Ascension Day
        easter + timedelta(days=49), # Whit Sunday
        easter + timedelta(days=50), # Whit Monday
        date(year, 12, 25),          # Christmas Day
        date(year, 12, 26),          # Boxing Day
    }


def is_day_tariff(now: datetime) -> bool:
    """Return True when Lnett's day tariff applies.

    Lnett defines day tariff as Monday-Friday 06:00-22:00.
    Saturdays, Sundays and public holidays use night/weekend tariff.
    """
    local_date = now.date()

    if local_date in norwegian_public_holidays(local_date.year):
        return False

    # Monday=0 ... Sunday=6
    if now.weekday() >= 5:
        return False

    return 6 <= now.hour < 22
