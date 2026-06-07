"""mh catalog build: assemble catalog.json from build results (spec §10, §13)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from forge.cli.main import cli
from tests.cli.conftest import FakeProducer


def test_catalog_build_writes_json(
    catalog_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("forge.cli.main.get_producer", lambda kind: FakeProducer())
    out = tmp_path / "catalog.json"
    res = CliRunner().invoke(
        cli,
        ["catalog", "build", "--all", "--catalog-root", str(catalog_root), "--output", str(out)],
    )
    assert res.exit_code == 0
    data = json.loads(out.read_text())
    assert data["schema_version"] == 1
    assert data["items"][0]["name"] == "node_exporter"
    assert data["items"][0]["new"] is True


def test_catalog_build_diffs_previous(
    catalog_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("forge.cli.main.get_producer", lambda kind: FakeProducer())
    previous = tmp_path / "prev.json"
    previous.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "t0",
                "items": [
                    {
                        "kind": "exporter",
                        "name": "node_exporter",
                        "version": "0.0.1",
                        "category": "System",
                        "description": "d",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "catalog.json"
    res = CliRunner().invoke(
        cli,
        [
            "catalog",
            "build",
            "--all",
            "--catalog-root",
            str(catalog_root),
            "--previous",
            str(previous),
            "--output",
            str(out),
        ],
    )
    assert res.exit_code == 0
    item = json.loads(out.read_text())["items"][0]
    assert item["new"] is False
    assert item["updated"] is True


def test_catalog_build_single_ref(
    catalog_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("forge.cli.main.get_producer", lambda kind: FakeProducer())
    out = tmp_path / "catalog.json"
    res = CliRunner().invoke(
        cli,
        [
            "catalog",
            "build",
            "node_exporter",
            "--catalog-root",
            str(catalog_root),
            "--output",
            str(out),
        ],
    )
    assert res.exit_code == 0
    assert json.loads(out.read_text())["items"][0]["name"] == "node_exporter"
