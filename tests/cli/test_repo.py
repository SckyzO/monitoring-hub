"""`mh repo build` CLI wiring: option parsing, --sign gating, param threading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from forge.cli.main import cli


def _catalog_file(tmp_path: Path) -> Path:
    catalog = {"schema_version": 1, "generated_at": "2026-06-07T00:00:00Z", "items": []}
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog))
    return path


def test_repo_build_sign_without_key_errors(tmp_path: Path) -> None:
    catalog = _catalog_file(tmp_path)
    result = CliRunner().invoke(
        cli,
        [
            "repo",
            "build",
            "--catalog",
            str(catalog),
            "--packages",
            str(tmp_path),
            "--dashboards",
            str(tmp_path),
            "--out",
            str(tmp_path / "public"),
            "--release-out",
            str(tmp_path / "release"),
            "--sign",
        ],
    )
    assert result.exit_code != 0
    assert "key-id" in result.output.lower()


def test_repo_build_missing_catalog_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli,
        [
            "repo",
            "build",
            "--catalog",
            str(tmp_path / "absent.json"),
            "--packages",
            str(tmp_path),
            "--dashboards",
            str(tmp_path),
            "--out",
            str(tmp_path / "public"),
            "--release-out",
            str(tmp_path / "release"),
        ],
    )
    assert result.exit_code != 0
    assert "catalog" in result.output.lower()


def test_repo_build_threads_params(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = _catalog_file(tmp_path)
    captured: dict[str, Any] = {}

    def fake_build_distribution(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return kwargs["catalog"]

    monkeypatch.setattr("forge.cli.main.build_distribution", fake_build_distribution)
    result = CliRunner().invoke(
        cli,
        [
            "repo",
            "build",
            "--catalog",
            str(catalog),
            "--packages",
            str(tmp_path),
            "--dashboards",
            str(tmp_path),
            "--out",
            str(tmp_path / "public"),
            "--release-out",
            str(tmp_path / "release"),
            "--package-base-url",
            "https://example/dl",
            "--pages-base-url",
            "https://example/pg",
            "--sign",
            "--key-id",
            "DEADBEEF",
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured["package_base_url"] == "https://example/dl"
    assert captured["pages_base_url"] == "https://example/pg"
    assert captured["key_id"] == "DEADBEEF"


def test_repo_build_unsigned_passes_no_key(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = _catalog_file(tmp_path)
    captured: dict[str, Any] = {}

    def fake_build_distribution(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return kwargs["catalog"]

    monkeypatch.setattr("forge.cli.main.build_distribution", fake_build_distribution)
    result = CliRunner().invoke(
        cli,
        [
            "repo",
            "build",
            "--catalog",
            str(catalog),
            "--packages",
            str(tmp_path),
            "--dashboards",
            str(tmp_path),
            "--out",
            str(tmp_path / "public"),
            "--release-out",
            str(tmp_path / "release"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert captured["key_id"] is None
