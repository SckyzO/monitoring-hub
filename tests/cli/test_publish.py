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


def _catalog_file_with_artifacts(tmp_path: Path) -> Path:
    catalog = {
        "schema_version": 1,
        "generated_at": "2026-06-15T00:00:00Z",
        "items": [
            {
                "kind": "exporter",
                "name": "node_exporter",
                "version": "1.12.0",
                "category": "System",
                "description": "d",
                "artifacts": [
                    {
                        "type": "rpm",
                        "target": "el9",
                        "arch": "amd64",
                        "sha256": "a" * 64,
                    },
                    {
                        "type": "deb",
                        "target": "ubuntu-24.04",
                        "arch": "amd64",
                        "sha256": "b" * 64,
                    },
                ],
            }
        ],
    }
    path = tmp_path / "catalog_with_arts.json"
    path.write_text(json.dumps(catalog))
    return path


class _SpyReleasesPrune:
    last: dict[str, Any] = {}

    def __init__(self, *, repo: str, runner: Any) -> None:
        _SpyReleasesPrune.last = {"repo": repo}

    def publish(self, staging: Path) -> None:
        _SpyReleasesPrune.last["staging"] = staging

    def prune(self, *, keep: dict[str, Any]) -> None:
        _SpyReleasesPrune.last["keep"] = keep


def test_publish_releases_prune_wires_keep_set(tmp_path: Path, monkeypatch: Any) -> None:
    """--prune calls prune() with a keep-set built from the catalogue artifacts."""
    catalog = _catalog_file_with_artifacts(tmp_path)
    # Non-empty releases dir so the upload path runs first.
    release_dir = tmp_path / "release"
    tag_dir = release_dir / "rpm-el9-x86_64"
    tag_dir.mkdir(parents=True)
    (tag_dir / "node_exporter-1.12.0-1.el9.x86_64.rpm").write_bytes(b"x")

    monkeypatch.setattr("forge.cli.main.GitHubReleasesPublisher", _SpyReleasesPrune)
    result = CliRunner().invoke(
        cli,
        [
            "publish",
            "--releases",
            str(release_dir),
            "--prune",
            "--catalog",
            str(catalog),
            "--repo",
            "o/r",
        ],
    )
    assert result.exit_code == 0, result.output
    keep = _SpyReleasesPrune.last["keep"]
    # RPM artifact → tag rpm-el9-x86_64
    assert "rpm-el9-x86_64" in keep
    assert "node_exporter-1.12.0-1.el9.x86_64.rpm" in keep["rpm-el9-x86_64"]
    # DEB artifact → tag apt-noble
    assert "apt-noble" in keep
    assert "node-exporter_1.12.0-1_amd64.deb" in keep["apt-noble"]


class _SpyArchive:
    """Spy for ArchiveReleasesPublisher: captures ctor args + publish_item calls."""

    last_keep: int = 0
    items: list[dict[str, Any]] = []

    def __init__(self, *, repo: str, runner: Any, keep: int) -> None:
        _SpyArchive.last_keep = keep
        _SpyArchive.items = []

    def publish_item(self, *, name: str, version: str, assets: list[Path]) -> None:
        _SpyArchive.items.append({"name": name, "version": version, "assets": assets})


def test_publish_archive_dispatches(tmp_path: Path, monkeypatch: Any) -> None:
    """--archive constructs ArchiveReleasesPublisher(keep=N) and calls publish_item
    for each built item (asset file present under --packages)."""
    catalog = _catalog_file(tmp_path)  # node_exporter 1.9.1

    # Create a matching .rpm under the packages tree
    pkg_dir = tmp_path / "dist"
    pkg_dir.mkdir()
    (pkg_dir / "node_exporter-1.9.1-1.el9.x86_64.rpm").write_bytes(b"x")

    monkeypatch.setattr("forge.cli.main.ArchiveReleasesPublisher", _SpyArchive)
    result = CliRunner().invoke(
        cli,
        [
            "publish",
            "--archive",
            "--packages",
            str(pkg_dir),
            "--catalog",
            str(catalog),
            "--keep",
            "5",
            "--repo",
            "o/r",
        ],
    )
    assert result.exit_code == 0, result.output
    assert _SpyArchive.last_keep == 5
    assert len(_SpyArchive.items) == 1
    assert _SpyArchive.items[0]["name"] == "node_exporter"
    assert _SpyArchive.items[0]["version"] == "1.9.1"
    assert len(_SpyArchive.items[0]["assets"]) > 0
