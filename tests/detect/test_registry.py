"""detect.registry: register/get/discover (mirrors kinds.registry) — spec §4."""

from __future__ import annotations

import pytest

from forge.detect.registry import (
    DetectRegistryError,
    all_sources,
    discover,
    get_source,
    register,
)


def test_register_and_get_source() -> None:
    @register("fake-source-a")
    class _FakeSourceA:
        type = "fake-source-a"

        def latest(self, manifest: object, *, runner: object) -> None:
            return None

    assert isinstance(get_source("fake-source-a"), _FakeSourceA)
    assert "fake-source-a" in all_sources()


def test_double_register_raises() -> None:
    @register("fake-source-b")
    class _FakeSourceB:
        type = "fake-source-b"

        def latest(self, manifest: object, *, runner: object) -> None:
            return None

    with pytest.raises(DetectRegistryError, match="already registered"):

        @register("fake-source-b")
        class _Dup:
            type = "fake-source-b"

            def latest(self, manifest: object, *, runner: object) -> None:
                return None


def test_get_unknown_source_raises() -> None:
    with pytest.raises(DetectRegistryError, match="no version source"):
        get_source("does-not-exist")


def test_discover_imports_without_error() -> None:
    discover()  # no real sources yet (SP4.1 adds github-release); must not raise
