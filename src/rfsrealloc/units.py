"""Units for transcribed inputs (pint) and dimensional checks at module boundaries.

Core numerical kernels operate on plain numbers in fixed units: volumes in billion
gallons, RIN quantities in billion gallon-RINs unless stated, standards in percent.
"""

from __future__ import annotations

from fractions import Fraction

import pint

ureg = pint.UnitRegistry()
ureg.define("RIN = [rin]")
ureg.define("gallon_RIN = RIN")
ureg.define("quad = 1e15 Btu")

_UNIT_MAP: dict[str, str] = {
    "billion gallons": "1e9 gallon",
    "million gallons": "1e6 gallon",
    "billion RINs": "1e9 RIN",
    "million RINs": "1e6 RIN",
    "RINs": "RIN",
    "percent": "percent",
    "fraction": "dimensionless",
    "count": "dimensionless",
    "years": "year",
    "dollars per RIN": "dollar / RIN",
    "dollars per gallon": "dollar / gallon",
    "cents per gallon": "0.01 dollar / gallon",
    "million barrels per day": "1e6 barrel / day",
    "quadrillion Btu": "quad",
    "million Btu per barrel": "1e6 Btu / barrel",
}

ureg.define("dollar = [currency]")


def quantity(value: float | Fraction | str, unit: str) -> pint.Quantity:
    """Return a pint quantity for a transcribed value and its unit label."""
    if unit not in _UNIT_MAP:
        raise KeyError(f"unknown transcribed unit label: {unit!r}")
    return ureg.Quantity(float(value), _UNIT_MAP[unit])


def is_volume(q: pint.Quantity) -> bool:
    return bool(q.check("[length] ** 3"))


def is_rin(q: pint.Quantity) -> bool:
    return bool(q.check("[rin]"))


def billion_gallons(q: pint.Quantity) -> float:
    if not is_volume(q):
        raise pint.DimensionalityError(q.units, "gallon")
    return float(q.to("gallon").magnitude / 1e9)


def billion_rins(q: pint.Quantity) -> float:
    if not is_rin(q):
        raise pint.DimensionalityError(q.units, "RIN")
    return float(q.to("RIN").magnitude / 1e9)


def mbd_to_billion_gallons_per_year(mbd: float, days: int = 365) -> float:
    """Million barrels per day to billion gallons per year (42 gallons per barrel)."""
    q: pint.Quantity = ureg.Quantity(mbd * 1e6, "barrel / day") * ureg.Quantity(days, "day")
    return billion_gallons(q)
