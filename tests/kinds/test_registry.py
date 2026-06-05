"""Kind registry: register / get_producer / all_kinds / discover (spec §9)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from forge.kinds import registry
from forge.kinds.base import BuildContext, BuildResult
from forge.kinds.registry import (
    KindRegistryError,
    all_kinds,
    discover,
    get_producer,
    register,
)


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    registry._REGISTRY.clear()


def _make_producer_cls(kind_name: str) -> type:
    @register(kind_name)
    class _P:
        kind = kind_name

        def validate(self, manifest: object) -> None:
            return None

        def build(self, manifest: object, ctx: BuildContext) -> BuildResult:
            raise NotImplementedError

    return _P


def test_register_and_get_returns_instance() -> None:
    _make_producer_cls("alpha")
    producer = get_producer("alpha")
    assert producer.kind == "alpha"


def test_all_kinds_is_sorted() -> None:
    _make_producer_cls("zebra")
    _make_producer_cls("alpha")
    assert all_kinds() == ["alpha", "zebra"]


def test_duplicate_registration_raises() -> None:
    _make_producer_cls("dup")
    with pytest.raises(KindRegistryError):
        _make_producer_cls("dup")


def test_get_unknown_kind_raises() -> None:
    with pytest.raises(KindRegistryError):
        get_producer("nope")


def test_discover_imports_submodules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = tmp_path / "fakekinds"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "beta.py").write_text(
        "from forge.kinds.registry import register\n"
        "@register('beta')\n"
        "class Beta:\n"
        "    kind = 'beta'\n"
        "    def validate(self, manifest): return None\n"
        "    def build(self, manifest, ctx): raise NotImplementedError\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    fakekinds = importlib.import_module("fakekinds")
    discover(fakekinds)
    assert "beta" in all_kinds()
