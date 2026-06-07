"""mh build: wire resolver → producer (spec §11, §13). No real nfpm/docker/network."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from forge.cli.main import cli
from tests.cli.conftest import FakeProducer


def test_build_invokes_producer(catalog_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("forge.cli.main.get_producer", lambda kind: FakeProducer())
    res = CliRunner().invoke(cli, ["build", "node_exporter", "--catalog-root", str(catalog_root)])
    assert res.exit_code == 0
    assert "rpm" in res.output
    assert "el9" in res.output


def test_build_applies_set_override(
    catalog_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, str] = {}

    class Capturing(FakeProducer):
        def build(self, manifest, ctx):  # type: ignore[no-untyped-def]
            captured["version"] = manifest.version
            return super().build(manifest, ctx)

    monkeypatch.setattr("forge.cli.main.get_producer", lambda kind: Capturing())
    res = CliRunner().invoke(
        cli,
        ["build", "node_exporter", "--catalog-root", str(catalog_root), "--set", "version=9.9.9"],
    )
    assert res.exit_code == 0
    assert captured["version"] == "9.9.9"


def test_build_passes_sign_key_into_context(
    catalog_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, str | None] = {}

    class Capturing(FakeProducer):
        def build(self, manifest, ctx):  # type: ignore[no-untyped-def]
            captured["key"] = ctx.signing_key_id
            return super().build(manifest, ctx)

    monkeypatch.setattr("forge.cli.main.get_producer", lambda kind: Capturing())
    res = CliRunner().invoke(
        cli,
        ["build", "node_exporter", "--catalog-root", str(catalog_root), "--sign-key", "ABCD"],
    )
    assert res.exit_code == 0
    assert captured["key"] == "ABCD"
