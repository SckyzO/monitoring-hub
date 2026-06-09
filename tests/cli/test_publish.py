"""`mh publish` CLI wiring: --oci dispatch, version threading, error paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from forge.cli.main import cli


def _catalog_file(tmp_path: Path) -> Path:
    catalog = {
        "schema_version": 1,
        "generated_at": "2026-06-07T00:00:00Z",
        "items": [
            {
                "kind": "exporter",
                "name": "node_exporter",
                "version": "1.9.1",
                "category": "System",
                "description": "d",
                "artifacts": [],
            }
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog))
    return path


class _SpyPublisher:
    last: dict[str, Any] = {}

    def __init__(self, *, registries: Any, versions: Any, runner: Any) -> None:
        _SpyPublisher.last = {"registries": tuple(registries), "versions": dict(versions)}

    def publish(self, staging: Path) -> None:
        _SpyPublisher.last["staging"] = staging


def test_publish_oci_dispatches(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = _catalog_file(tmp_path)
    monkeypatch.setattr("forge.cli.main.OciPublisher", _SpyPublisher)
    result = CliRunner().invoke(
        cli,
        [
            "publish",
            "--oci",
            "--registry",
            "ghcr.io/x/y",
            "--registry",
            "docker.io/x",
            "--contexts",
            str(tmp_path / "dist" / "docker"),
            "--catalog",
            str(catalog),
        ],
    )
    assert result.exit_code == 0, result.output
    assert _SpyPublisher.last["registries"] == ("ghcr.io/x/y", "docker.io/x")
    assert _SpyPublisher.last["versions"] == {"node_exporter": "1.9.1"}
    assert _SpyPublisher.last["staging"] == tmp_path / "dist" / "docker"


def test_publish_oci_defaults_to_ghcr(tmp_path: Path, monkeypatch: Any) -> None:
    catalog = _catalog_file(tmp_path)
    monkeypatch.setattr("forge.cli.main.OciPublisher", _SpyPublisher)
    result = CliRunner().invoke(
        cli,
        ["publish", "--oci", "--contexts", str(tmp_path / "d"), "--catalog", str(catalog)],
    )
    assert result.exit_code == 0, result.output
    assert _SpyPublisher.last["registries"] == ("ghcr.io/sckyzo/monitoring-hub",)


def test_publish_without_target_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli, ["publish", "--catalog", str(_catalog_file(tmp_path))])
    assert result.exit_code != 0
    assert "nothing to publish" in result.output.lower()


def test_publish_missing_catalog_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli, ["publish", "--oci", "--catalog", str(tmp_path / "absent.json")]
    )
    assert result.exit_code != 0
    assert "catalog" in result.output.lower()


class _SpyReleases:
    last: dict[str, Any] = {}

    def __init__(self, *, repo: str, runner: Any) -> None:
        _SpyReleases.last = {"repo": repo}

    def publish(self, staging: Path) -> None:
        _SpyReleases.last["staging"] = staging


def test_publish_releases_dispatches(tmp_path: Path, monkeypatch: Any) -> None:
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    monkeypatch.setattr("forge.cli.main.GitHubReleasesPublisher", _SpyReleases)
    result = CliRunner().invoke(cli, ["publish", "--releases", str(release_dir), "--repo", "o/r"])
    assert result.exit_code == 0, result.output
    assert _SpyReleases.last["repo"] == "o/r"
    assert _SpyReleases.last["staging"] == release_dir
