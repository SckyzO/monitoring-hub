"""CLI tests for `mh catalog reconcile` (wires reconcile.missing_legs)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from forge.cli.main import cli


def _write_manifest(root: Path, name: str) -> None:
    d = root / "exporters" / name
    d.mkdir(parents=True)
    (d / "manifest.yaml").write_text(
        "\n".join(
            [
                "kind: exporter",
                f"name: {name}",
                "version: 1.0.0",
                f"description: {name}",
                "category: System",
                "spec:",
                "  upstream:",
                "    type: github",
                "    repo: owner/" + name,
                "  build:",
                "    method: binary_repack",
                "    binary_name: " + name,
                "    archs: [amd64]",
                "  artifacts:",
                "    rpm:",
                "      enabled: true",
                "      targets: [el9]",
                "    deb:",
                "      enabled: false",
                "    docker:",
                "      enabled: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_catalog(path: Path, *, items: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-06-09T00:00:00Z",
                "items": items,
            }
        ),
        encoding="utf-8",
    )


def _entry(name: str, *, artifacts: list[dict[str, object]]) -> dict[str, object]:
    return {
        "name": name,
        "kind": "exporter",
        "version": "1.0.0",
        "description": name,
        "category": "System",
        "artifacts": artifacts,
    }


def _rpm_art() -> dict[str, object]:
    return {
        "type": "rpm",
        "target": "el9",
        "arch": "amd64",
        "sha256": "0" * 64,
        "signed": True,
    }


def test_reconcile_all_present_is_empty(tmp_path: Path) -> None:
    root = tmp_path / "catalog"
    _write_manifest(root, "node_exporter")
    cat = tmp_path / "catalog.json"
    _write_catalog(cat, items=[_entry("node_exporter", artifacts=[_rpm_art()])])

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["catalog", "reconcile", "--catalog-root", str(root), "--catalog", str(cat), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {"missing": [], "items": []}


def test_reconcile_one_missing_leg(tmp_path: Path) -> None:
    root = tmp_path / "catalog"
    _write_manifest(root, "node_exporter")  # expects rpm/el9/amd64
    cat = tmp_path / "catalog.json"
    _write_catalog(cat, items=[_entry("node_exporter", artifacts=[])])  # nothing present

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["catalog", "reconcile", "--catalog-root", str(root), "--catalog", str(cat), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["items"] == ["node_exporter"]
    assert payload["missing"] == [
        {"item": "node_exporter", "type": "rpm", "target": "el9", "arch": "amd64"}
    ]


def test_reconcile_no_catalog_means_all_expected(tmp_path: Path) -> None:
    root = tmp_path / "catalog"
    _write_manifest(root, "node_exporter")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["catalog", "reconcile", "--catalog-root", str(root), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["items"] == ["node_exporter"]


def test_reconcile_human_summary(tmp_path: Path) -> None:
    root = tmp_path / "catalog"
    _write_manifest(root, "node_exporter")
    cat = tmp_path / "catalog.json"
    _write_catalog(cat, items=[_entry("node_exporter", artifacts=[])])
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["catalog", "reconcile", "--catalog-root", str(root), "--catalog", str(cat)],
    )
    assert result.exit_code == 0, result.output
    assert "node_exporter" in result.output
    assert "rpm" in result.output
    assert "el9" in result.output
