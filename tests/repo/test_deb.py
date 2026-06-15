"""APT flat repo generation: apt-ftparchive Packages + Release."""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import cast

import pytest

from forge.domain.errors import DistributionError
from forge.packaging.runner import CommandResult
from forge.repo.deb import build_apt_repo, merge_apt_repo, merge_packages
from tests.packaging.conftest import FakeRunner


def _deb(path: Path, name: str) -> Path:
    pkg = path / name
    pkg.write_bytes(b"deb")
    return pkg


def test_build_apt_repo_emits_packages_then_release(tmp_path: Path) -> None:
    deb = _deb(tmp_path, "node-exporter_1.9.1-1_amd64.deb")
    repo_dir = tmp_path / "release" / "apt-noble"
    runner = FakeRunner(
        [
            CommandResult(args=[], returncode=0, stdout="Package: node-exporter\n", stderr=""),
            CommandResult(args=[], returncode=0, stdout="Origin: monitoring-hub\n", stderr=""),
        ]
    )
    out = build_apt_repo(
        packages=[deb],
        repo_dir=repo_dir,
        codename="noble",
        origin="monitoring-hub",
        runner=runner,
    )
    assert out == repo_dir

    pkg_call = cast("list[str]", runner.calls[0]["args"])
    assert pkg_call == ["apt-ftparchive", "packages", "."]
    assert runner.calls[0]["cwd"] == repo_dir

    rel_call = cast("list[str]", runner.calls[1]["args"])
    assert rel_call[0] == "apt-ftparchive"
    assert rel_call[-2:] == ["release", "."]
    assert "APT::FTPArchive::Release::Codename=noble" in rel_call
    assert "APT::FTPArchive::Release::Origin=monitoring-hub" in rel_call
    assert runner.calls[1]["cwd"] == repo_dir


def test_build_apt_repo_materializes_flat_tree(tmp_path: Path) -> None:
    deb = _deb(tmp_path, "node-exporter_1.9.1-1_amd64.deb")
    repo_dir = tmp_path / "release" / "apt-noble"
    runner = FakeRunner(
        [
            CommandResult(args=[], returncode=0, stdout="Package: node-exporter\n", stderr=""),
            CommandResult(args=[], returncode=0, stdout="Origin: monitoring-hub\n", stderr=""),
        ]
    )
    build_apt_repo(
        packages=[deb],
        repo_dir=repo_dir,
        codename="noble",
        origin="monitoring-hub",
        runner=runner,
    )
    # .deb copied flat (no pool/) and kept (whole flat repo ships to Releases).
    assert (repo_dir / "node-exporter_1.9.1-1_amd64.deb").exists()
    assert not (repo_dir / "pool").exists()
    # Packages from apt-ftparchive stdout, plus its gzip.
    assert (repo_dir / "Packages").read_text() == "Package: node-exporter\n"
    assert gzip.decompress((repo_dir / "Packages.gz").read_bytes()) == b"Package: node-exporter\n"
    # Release from the second apt-ftparchive stdout.
    assert (repo_dir / "Release").read_text() == "Origin: monitoring-hub\n"
    # Source untouched.
    assert deb.exists()


def test_build_apt_repo_rejects_empty_input(tmp_path: Path) -> None:
    with pytest.raises(DistributionError, match="no deb"):
        build_apt_repo(
            packages=[],
            repo_dir=tmp_path / "apt-noble",
            codename="noble",
            origin="monitoring-hub",
            runner=FakeRunner(),
        )


def test_build_apt_repo_raises_on_apt_ftparchive_failure(tmp_path: Path) -> None:
    deb = _deb(tmp_path, "node-exporter_1.9.1-1_amd64.deb")
    runner = FakeRunner(
        [CommandResult(args=["apt-ftparchive"], returncode=1, stdout="", stderr="scan failed")]
    )
    with pytest.raises(DistributionError, match="scan failed"):
        build_apt_repo(
            packages=[deb],
            repo_dir=tmp_path / "apt-noble",
            codename="noble",
            origin="monitoring-hub",
            runner=runner,
        )


def test_build_apt_repo_raises_on_release_failure(tmp_path: Path) -> None:
    deb = _deb(tmp_path, "node-exporter_1.9.1-1_amd64.deb")
    runner = FakeRunner(
        [
            CommandResult(args=["apt-ftparchive"], returncode=0, stdout="Package: x\n", stderr=""),
            CommandResult(args=["apt-ftparchive"], returncode=1, stdout="", stderr="release boom"),
        ]
    )
    with pytest.raises(DistributionError, match="release boom"):
        build_apt_repo(
            packages=[deb],
            repo_dir=tmp_path / "apt-noble",
            codename="noble",
            origin="monitoring-hub",
            runner=runner,
        )


def test_merge_packages_replaces_changed_keeps_others() -> None:
    node_old = (
        "Package: node-exporter\nVersion: 1.11.1-1\nFilename: ./node-exporter_1.11.1-1_amd64.deb\n"
    )
    mysql = (
        "Package: mysqld-exporter\n"
        "Version: 0.15.0-1\n"
        "Filename: ./mysqld-exporter_0.15.0-1_amd64.deb\n"
    )
    published = f"{node_old}\n{mysql}\n"
    new_stanza = (
        "Package: node-exporter\nVersion: 1.12.0-1\nFilename: ./node-exporter_1.12.0-1_amd64.deb\n"
    )
    out = merge_packages(published=published, new_stanza=new_stanza, package="node-exporter")
    stanzas = [s for s in out.split("\n\n") if s.strip()]
    assert len(stanzas) == 2
    assert "Version: 1.12.0-1" in out and "Version: 1.11.1-1" not in out
    assert "mysqld-exporter" in out


def test_merge_packages_appends_when_new_package() -> None:
    published = "Package: mysqld-exporter\nVersion: 0.15.0-1\n"
    new_stanza = "Package: node-exporter\nVersion: 1.12.0-1\n"
    out = merge_packages(published=published, new_stanza=new_stanza, package="node-exporter")
    assert "mysqld-exporter" in out and "node-exporter" in out


def test_merge_apt_repo_records_new_deb_and_regenerates(tmp_path: Path) -> None:
    new = _deb(tmp_path, "node-exporter_1.12.0-1_amd64.deb")
    published = tmp_path / "pub" / "Packages"
    published.parent.mkdir(parents=True)
    node_old = (
        "Package: node-exporter\nVersion: 1.11.1-1\nFilename: ./node-exporter_1.11.1-1_amd64.deb\n"
    )
    mysql = (
        "Package: mysqld-exporter\n"
        "Version: 0.15.0-1\n"
        "Filename: ./mysqld-exporter_0.15.0-1_amd64.deb\n"
    )
    published.write_text(f"{node_old}\n{mysql}")
    repo_dir = tmp_path / "release" / "apt-noble"
    node_new_stanza = (
        "Package: node-exporter\nVersion: 1.12.0-1\nFilename: ./node-exporter_1.12.0-1_amd64.deb\n"
    )
    runner = FakeRunner(
        [
            CommandResult(args=[], returncode=0, stdout=node_new_stanza, stderr=""),
            CommandResult(args=[], returncode=0, stdout="Origin: monitoring-hub\n", stderr=""),
        ]
    )
    out = merge_apt_repo(
        new_package=new,
        published_packages=published,
        repo_dir=repo_dir,
        codename="noble",
        origin="monitoring-hub",
        runner=runner,
    )
    assert out == repo_dir
    merged = (repo_dir / "Packages").read_text()
    assert "Version: 1.12.0-1" in merged and "Version: 1.11.1-1" not in merged
    assert "mysqld-exporter" in merged
    assert (repo_dir / "Packages.gz").is_file()
    assert (repo_dir / "Release").read_text() == "Origin: monitoring-hub\n"
