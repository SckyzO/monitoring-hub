"""In-tree version-source registry (spec §4), mirroring ``forge.kinds.registry``.

``@register("github-release")`` adds a source instance to a module-level dict;
``get_source(type)`` returns it; ``discover()`` pkgutil-imports every submodule of
``forge.detect`` so ``@register`` side effects fire on import — no central list to
edit when a source type is added.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from types import ModuleType
from typing import TypeVar

import forge.detect as _detect_package
from forge.detect.base import VersionSource
from forge.domain.errors import ForgeError

S = TypeVar("S", bound=VersionSource)

_REGISTRY: dict[str, VersionSource] = {}


class DetectRegistryError(ForgeError):
    """A version source is double-registered or requested without a registration."""


def register(source_type: str) -> Callable[[type[S]], type[S]]:
    """Class decorator registering a version-source instance under ``source_type``."""

    def decorator(source_cls: type[S]) -> type[S]:
        if source_type in _REGISTRY:
            raise DetectRegistryError(f"source {source_type!r} is already registered")
        _REGISTRY[source_type] = source_cls()
        return source_cls

    return decorator


def get_source(source_type: str) -> VersionSource:
    try:
        return _REGISTRY[source_type]
    except KeyError as exc:
        raise DetectRegistryError(f"no version source registered for {source_type!r}") from exc


def all_sources() -> list[str]:
    return sorted(_REGISTRY)


def discover(package: ModuleType | None = None) -> None:
    """Import every submodule of ``package`` (default ``forge.detect``) so the
    ``@register`` decorators run."""
    resolved: ModuleType = package if package is not None else _detect_package
    for info in pkgutil.iter_modules(resolved.__path__, resolved.__name__ + "."):
        importlib.import_module(info.name)
