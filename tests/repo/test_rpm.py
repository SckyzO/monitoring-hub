"""RPM repo generation: filename grouping + createrepo_c invocation."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.domain.errors import DistributionError
from forge.packaging.runner import CommandResult
from forge.repo.rpm import build_rpm_repo, group_rpms_by_target_arch
from tests.packaging.conftest import FakeRunner


def test_group_splits_by_target_and_arch() -> None:
    packages = [
        Path("node_exporter-1.9.1-1.el9.x86_64.rpm"),
        Path("node_exporter-1.9.1-1.el9.aarch64.rpm"),
        Path("node_exporter-1.9.1-1.el10.x86_64.rpm"),
        Path("mysqld_exporter-0.15.0-1.el9.x86_64.rpm"),
    ]
    groups = group_rpms_by_target_arch(packages)
    assert set(groups) == {("el9", "x86_64"), ("el9", "aarch64"), ("el10", "x86_64")}
    assert len(groups[("el9", "x86_64")]) == 2  # node + mysqld


def test_group_rejects_a_non_rpm_filename() -> None:
    with pytest.raises(DistributionError, match="cannot parse"):
        group_rpms_by_target_arch([Path("not-a-package.txt")])


def test_group_rejects_an_unknown_arch() -> None:
    with pytest.raises(DistributionError, match="cannot parse"):
        group_rpms_by_target_arch([Path("x-1-1.el9.sparc64.rpm")])


def _rpm(path: Path, name: str) -> Path:
    pkg = path / name
    pkg.write_bytes(b"rpm")
    return pkg


def test_build_rpm_repo_invokes_createrepo_with_location_prefix(tmp_path: Path) -> None:
    pkg = _rpm(tmp_path, "node_exporter-1.9.1-1.el9.x86_64.rpm")
    repodata_dir = tmp_path / "public" / "el9" / "x86_64" / "repodata"
    runner = FakeRunner()
    out = build_rpm_repo(
        packages=[pkg],
        repodata_dir=repodata_dir,
        location_prefix="https://github.com/SckyzO/monitoring-hub/releases/download",
        runner=runner,
    )
    assert out == repodata_dir
    args = cast("list[str]", runner.calls[0]["args"])
    assert args[0] == "createrepo_c"
    assert "--location-prefix" in args
    prefix_value = args[args.index("--location-prefix") + 1]
    assert prefix_value == "https://github.com/SckyzO/monitoring-hub/releases/download"
    # createrepo_c runs against the work dir = the repodata dir's parent.
    assert str(repodata_dir.parent) in args


def test_build_rpm_repo_stages_then_removes_the_rpms(tmp_path: Path) -> None:
    pkg = _rpm(tmp_path, "node_exporter-1.9.1-1.el9.x86_64.rpm")
    repodata_dir = tmp_path / "public" / "el9" / "x86_64" / "repodata"
    build_rpm_repo(
        packages=[pkg],
        repodata_dir=repodata_dir,
        location_prefix="https://example/releases",
        runner=FakeRunner(),
    )
    # The Pages tree must not carry the blobs; they go to Releases.
    assert list(repodata_dir.parent.glob("*.rpm")) == []
    # The source package is untouched.
    assert pkg.exists()


def test_build_rpm_repo_rejects_empty_input(tmp_path: Path) -> None:
    with pytest.raises(DistributionError, match="no rpm"):
        build_rpm_repo(
            packages=[],
            repodata_dir=tmp_path / "repodata",
            location_prefix="https://example/releases",
            runner=FakeRunner(),
        )


def test_build_rpm_repo_raises_on_createrepo_failure(tmp_path: Path) -> None:
    pkg = _rpm(tmp_path, "node_exporter-1.9.1-1.el9.x86_64.rpm")
    runner = FakeRunner(
        [CommandResult(args=["createrepo_c"], returncode=1, stdout="", stderr="boom")]
    )
    with pytest.raises(DistributionError, match="boom"):
        build_rpm_repo(
            packages=[pkg],
            repodata_dir=tmp_path / "el9" / "x86_64" / "repodata",
            location_prefix="https://example/releases",
            runner=runner,
        )


def test_build_rpm_repo_offline_omits_prefix_and_keeps(tmp_path: Path) -> None:
    work = tmp_path / "yum" / "el9" / "x86_64"
    work.mkdir(parents=True)
    rpm = work / "node_exporter-1.9.1-1.el9.x86_64.rpm"
    rpm.write_text("RPM", encoding="utf-8")
    runner = FakeRunner()

    build_rpm_repo(
        packages=[rpm],
        repodata_dir=work / "repodata",
        location_prefix="",
        keep_packages=True,
        runner=runner,
    )
    assert cast("list[str]", runner.calls[0]["args"]) == ["createrepo_c", str(work)]
    assert rpm.is_file()


def test_build_rpm_repo_split_still_removes_blobs(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    rpm = src / "node_exporter-1.9.1-1.el9.x86_64.rpm"
    rpm.write_text("RPM", encoding="utf-8")
    out = tmp_path / "public" / "el9" / "x86_64"
    runner = FakeRunner()

    build_rpm_repo(
        packages=[rpm],
        repodata_dir=out / "repodata",
        location_prefix="https://x/rpm-el9-x86_64/",
        runner=runner,
    )
    assert cast("list[str]", runner.calls[0]["args"]) == [
        "createrepo_c",
        "--location-prefix",
        "https://x/rpm-el9-x86_64/",
        str(out),
    ]
    assert not (out / rpm.name).exists()
    assert rpm.is_file()
