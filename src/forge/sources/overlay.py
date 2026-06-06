"""Override-overlay: deep-merge partial overlays and --set onto base data (spec §8)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` onto ``base``, returning a new dict.

    Mappings are merged key by key; any non-mapping value (scalars and lists)
    in ``overlay`` replaces the base value. Inputs are not mutated.
    """
    result: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        existing = result.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            result[key] = deep_merge(existing, value)
        else:
            result[key] = value
    return result
