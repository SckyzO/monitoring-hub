"""Artefact sources: local tree + published Releases/Pages (spec §5.3)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge.bundle.resolver import ResolvedArtifact
from forge.bundle.source import LocalDirSource, ReleasesFetcher, _release_tag
from forge.domain.artifact import Artifact
from forge.domain.errors import BundleError
from forge.packaging.runner import CommandResult


def _rpm() -> ResolvedArtifact:
    return ResolvedArtifact(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        artifact=Artifact(type="rpm", target="el9", arch="amd64", sha256="a"),
        filename="node_exporter-1.9.1-1.el9.x86_64.rpm",
    )


def _deb() -> ResolvedArtifact:
    return ResolvedArtifact(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        artifact=Artifact(type="deb", target="ubuntu-24.04", arch="amd64", sha256="c"),
        filename="node-exporter_1.9.1-1_amd64.deb",
    )


def _dashboard() -> ResolvedArtifact:
    return ResolvedArtifact(
        kind="dashboard",
        name="node-overview",
        version="39",
        artifact=Artifact(
            type="grafana-dashboard",
            sha256="x",
            url="https://sckyzo.github.io/monitoring-hub/dashboards/node-overview.json",
        ),
        filename="node-overview.json",
    )


class _GhRunner:
    """Fake CommandRunner: records argv; on `gh release download` writes the
    asset into --dir so the fetcher's move-to-dest is exercised."""

    def __init__(self, returncode: int = 0) -> None:
        self.calls: list[list[str]] = []
        self._returncode = returncode

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        arg_list = list(args)
        self.calls.append(arg_list)
        if self._returncode == 0 and arg_list[:3] == ["gh", "release", "download"]:
            out_dir = Path(arg_list[arg_list.index("--dir") + 1])
            pattern = arg_list[arg_list.index("--pattern") + 1]
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / pattern).write_text("BLOB", encoding="utf-8")
        return CommandResult(args=arg_list, returncode=self._returncode, stdout="", stderr="boom")


class _RecordingDownloader:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Path]] = []

    def download(self, url: str, dest: Path) -> Path:
        self.calls.append((url, dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("DASH", encoding="utf-8")
        return dest


def test_local_dir_source_copies_match(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    nested = root / "rpm-el9"
    nested.mkdir(parents=True)
    (nested / "node_exporter-1.9.1-1.el9.x86_64.rpm").write_text("RPM", encoding="utf-8")
    dest = tmp_path / "out" / "node_exporter-1.9.1-1.el9.x86_64.rpm"

    got = LocalDirSource(root).fetch(_rpm(), dest)
    assert got == dest
    assert dest.read_text(encoding="utf-8") == "RPM"


def test_local_dir_source_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(BundleError, match="not found"):
        LocalDirSource(tmp_path).fetch(_rpm(), tmp_path / "out.rpm")


def test_releases_fetcher_rpm_gh_argv_and_move(tmp_path: Path) -> None:
    runner = _GhRunner()
    dest = tmp_path / "yum" / "node_exporter-1.9.1-1.el9.x86_64.rpm"
    got = ReleasesFetcher(
        repo="SckyzO/monitoring-hub", runner=runner, downloader=_RecordingDownloader()
    ).fetch(_rpm(), dest)
    assert got == dest
    assert dest.read_text(encoding="utf-8") == "BLOB"
    assert runner.calls[0] == [
        "gh",
        "release",
        "download",
        "rpm-el9-x86_64",
        "--pattern",
        "node_exporter-1.9.1-1.el9.x86_64.rpm",
        "--dir",
        str(dest.parent),
        "--repo",
        "SckyzO/monitoring-hub",
    ]


def test_releases_fetcher_deb_tag(tmp_path: Path) -> None:
    runner = _GhRunner()
    dest = tmp_path / "apt" / "node-exporter_1.9.1-1_amd64.deb"
    ReleasesFetcher(repo="r", runner=runner, downloader=_RecordingDownloader()).fetch(_deb(), dest)
    assert runner.calls[0][3] == "apt-noble"


def test_releases_fetcher_gh_failure_raises(tmp_path: Path) -> None:
    with pytest.raises(BundleError, match="gh release download"):
        ReleasesFetcher(
            repo="r", runner=_GhRunner(returncode=1), downloader=_RecordingDownloader()
        ).fetch(_rpm(), tmp_path / "x.rpm")


def test_releases_fetcher_dashboard_uses_url(tmp_path: Path) -> None:
    dl = _RecordingDownloader()
    dest = tmp_path / "dashboards" / "node-overview.json"
    ReleasesFetcher(repo="r", runner=_GhRunner(), downloader=dl).fetch(_dashboard(), dest)
    assert dl.calls == [
        ("https://sckyzo.github.io/monitoring-hub/dashboards/node-overview.json", dest)
    ]
    assert dest.read_text(encoding="utf-8") == "DASH"


def test_releases_fetcher_dashboard_missing_url_raises(tmp_path: Path) -> None:
    art = ResolvedArtifact(
        kind="dashboard",
        name="d",
        version="1",
        artifact=Artifact(type="grafana-dashboard", sha256="x"),
        filename="d.json",
    )
    with pytest.raises(BundleError, match="no url"):
        ReleasesFetcher(repo="r", runner=_GhRunner(), downloader=_RecordingDownloader()).fetch(
            art, tmp_path / "d.json"
        )


def test_release_tag_rejects_non_package_type() -> None:
    docker = ResolvedArtifact(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        artifact=Artifact(type="docker", target="node_exporter:1.9.1", sha256="d"),
        filename="node_exporter:1.9.1",
    )
    with pytest.raises(BundleError, match="no release tag"):
        _release_tag(docker)
