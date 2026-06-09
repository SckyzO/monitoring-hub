"""mh watch CLI: --json shape + human output (spec §8)."""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from forge.cli.main import cli
from forge.detect.base import DetectedVersion


@pytest.fixture
def _patched(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_detect_all(manifests: object, *, runner: object) -> list[DetectedVersion]:
        return [
            DetectedVersion(
                item="demo_exporter",
                kind="exporter",
                current="1.9.0",
                latest="1.10.0",
                latest_raw="v1.10.0",
                source_type="github-release",
                outdated=True,
            )
        ]

    monkeypatch.setattr("forge.cli.main.detect_all", fake_detect_all)
    monkeypatch.setattr("forge.cli.main.discover_sources", lambda: None)


@pytest.mark.usefixtures("_patched")
def test_watch_json_shape() -> None:
    result = CliRunner().invoke(cli, ["watch", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == [
        {
            "item": "demo_exporter",
            "kind": "exporter",
            "current": "1.9.0",
            "latest": "1.10.0",
            "latest_raw": "v1.10.0",
            "source_type": "github-release",
            "outdated": True,
        }
    ]


@pytest.mark.usefixtures("_patched")
def test_watch_human_output() -> None:
    result = CliRunner().invoke(cli, ["watch"])
    assert result.exit_code == 0, result.output
    assert "demo_exporter" in result.output
    assert "1.9.0" in result.output
    assert "1.10.0" in result.output
