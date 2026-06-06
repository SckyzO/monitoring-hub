"""Override-overlay: deep-merge partial overlays and --set onto base data (spec §8)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import yaml

from forge.domain.errors import SourceResolutionError


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


def parse_set_override(expr: str) -> dict[str, Any]:
    """Parse a ``field.path=value`` override into a nested dict.

    The value is parsed with ``yaml.safe_load`` so it gets a natural YAML scalar
    type (``true`` → bool, ``39`` → int, ``/usr/bin/x`` → str), consistent with
    the manifest format itself.
    """
    path, sep, raw = expr.partition("=")
    if not sep:
        raise SourceResolutionError(f"--set expects KEY=VALUE, got: {expr!r}")
    keys = path.split(".")
    if any(not key for key in keys):
        raise SourceResolutionError(f"--set has an empty key segment: {expr!r}")
    value: Any = yaml.safe_load(raw)
    *parents, leaf = keys
    nested: dict[str, Any] = {leaf: value}
    for key in reversed(parents):
        nested = {key: nested}
    return nested


def apply_set_overrides(base: Mapping[str, Any], exprs: Sequence[str]) -> dict[str, Any]:
    """Deep-merge a sequence of ``field.path=value`` overrides onto ``base``."""
    result: dict[str, Any] = dict(base)
    for expr in exprs:
        result = deep_merge(result, parse_set_override(expr))
    return result
