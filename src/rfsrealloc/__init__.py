"""Exact reconstruction of Renewable Fuel Standard percentage standards and analysis of
small-refinery-exemption reallocation timing rules."""

from __future__ import annotations

__version__ = "1.0.2"

CATEGORIES: tuple[str, ...] = ("CB", "BBD", "AB", "RF")
"""Statutory categories: cellulosic biofuel, biomass-based diesel, advanced biofuel,
total renewable fuel (nested in that order)."""

REALLOCATED_CATEGORIES: tuple[str, ...] = ("BBD", "AB", "RF")
"""Categories for which EPA establishes SRE reallocation volumes (no cellulosic SRERV)."""

ALTERNATIVES: tuple[str, ...] = ("set2", "equal", "all2027")
"""Set 2 rule standards (existing), equal reallocation, and all-in-2027 reallocation."""
