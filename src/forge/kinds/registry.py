"""In-tree kind registry (spec §9).

``@register("exporter")`` adds a producer instance to a module-level dict;
``get_producer(kind)`` returns it. ``discover()`` pkgutil-imports every
submodule of a package so its ``@register`` side effects fire on import — no
central list to edit when a kind is added ("extensibility without modifying the
core").
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from types import ModuleType
from typing import TypeVar

import forge.kinds as _kinds_package
from forge.domain.errors import ForgeError
from forge.kinds.base import Producer

P = TypeVar("P", bound=Producer)

_REGISTRY: dict[str, Producer] = {}


class KindRegistryError(ForgeError):
    """A kind is double-registered or requested without a producer."""


def register(kind: str) -> Callable[[type[P]], type[P]]:
    """Class decorator registering a producer instance under ``kind``."""

    def decorator(producer_cls: type[P]) -> type[P]:
        if kind in _REGISTRY:
            raise KindRegistryError(f"kind {kind!r} is already registered")
        _REGISTRY[kind] = producer_cls()
        return producer_cls

    return decorator


def get_producer(kind: str) -> Producer:
    try:
        return _REGISTRY[kind]
    except KeyError as exc:
        raise KindRegistryError(f"no producer registered for kind {kind!r}") from exc


def all_kinds() -> list[str]:
    return sorted(_REGISTRY)


def discover(package: ModuleType | None = None) -> None:
    """Import every submodule of ``package`` (default: ``forge.kinds``) so the
    ``@register`` decorators run."""
    resolved: ModuleType = package if package is not None else _kinds_package
    for info in pkgutil.iter_modules(resolved.__path__, resolved.__name__ + "."):
        importlib.import_module(info.name)
