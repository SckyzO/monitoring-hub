"""NfpmPackager adapter: faked-runner orchestration + a real-nfpm POC."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from forge.domain.artifact import Artifact
from forge.domain.errors import BuildError
from forge.domain.manifest import (
    Build,
    Directory,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    RpmTarget,
    Upstream,
)
from forge.packaging.checksum import file_sha256
from forge.packaging.nfpm import NfpmPackager
from forge.packaging.runner import CommandResult, SubprocessRunner
from tests.packaging.conftest import FakeRunner


class _WritingRunner(FakeRunner):
    """FakeRunner that materializes a file so the post-build glob finds output."""

    def __init__(self, output: Path) -> None:
        super().__init__()
        self._output = output

    def run(
        self,
        args: Any,
        *,
        cwd: Any = None,
        env: Any = None,
        stdin: Any = None,
    ) -> CommandResult:
        self._output.write_bytes(b"pkgdata")
        return super().run(args, cwd=cwd, env=env, stdin=stdin)


def _binary(tmp_path: Path) -> Path:
    b = tmp_path / "node_exporter"
    b.write_bytes(b"\x7fELF-fake")
    return b


def test_package_writes_config_and_invokes_nfpm(manifest: ExporterManifest, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    # nfpm "produces" a file as a side effect; fake it by having the runner
    # create the output, then return rc=0.
    out = work / "node_exporter-1.9.1-1.el9.x86_64.rpm"

    class WritingRunner(FakeRunner):
        def run(
            self,
            args: Any,
            *,
            cwd: Any = None,
            env: Any = None,
            stdin: Any = None,
        ) -> CommandResult:
            out.write_bytes(b"rpmdata")
            return super().run(args, cwd=cwd, env=env, stdin=stdin)

    runner = WritingRunner()
    packager = NfpmPackager(runner)
    artifact = packager.package(
        manifest,
        packager="rpm",
        target="el9",
        arch="amd64",
        binary_src=_binary(tmp_path),
        work_dir=work,
    )

    assert isinstance(artifact, Artifact)
    assert artifact.type == "rpm"
    assert artifact.target == "el9"
    assert artifact.arch == "amd64"
    assert artifact.signed is False
    assert artifact.sha256 == file_sha256(out)

    # config + scriptlets + unit were written to work_dir
    assert (work / "nfpm.yaml").is_file()
    assert (work / "node_exporter.service").is_file()
    assert (work / "postinstall.sh").is_file()

    # nfpm was called with -p rpm and -f <config>
    call = cast("list[str]", runner.calls[0]["args"])
    assert call[0].endswith("nfpm")
    assert "-p" in call and "rpm" in call
    assert "-f" in call


def test_package_raises_build_error_on_nonzero(manifest: ExporterManifest, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    runner = FakeRunner([CommandResult(args=["nfpm"], returncode=1, stdout="", stderr="boom")])
    with pytest.raises(BuildError, match="boom"):
        NfpmPackager(runner).package(
            manifest,
            packager="rpm",
            target="el9",
            arch="amd64",
            binary_src=_binary(tmp_path),
            work_dir=work,
        )


def test_package_deb_uses_normalized_name(manifest: ExporterManifest, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    out = work / "node-exporter_1.9.1_arm64.deb"

    class WritingRunner(FakeRunner):
        def run(
            self,
            args: Any,
            *,
            cwd: Any = None,
            env: Any = None,
            stdin: Any = None,
        ) -> CommandResult:
            out.write_bytes(b"debdata")
            return super().run(args, cwd=cwd, env=env, stdin=stdin)

    artifact = NfpmPackager(WritingRunner()).package(
        manifest,
        packager="deb",
        target="ubuntu-24.04",
        arch="arm64",
        binary_src=_binary(tmp_path),
        work_dir=work,
    )
    assert artifact.type == "deb"
    assert artifact.target == "ubuntu-24.04"


def test_package_threads_directories(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    manifest = ExporterManifest(
        kind="exporter",
        name="x_exp",
        description="d",
        version="1.0.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="o/r"),
            build=Build(method="binary_repack", binary_name="x_exp"),
            artifacts=ExporterArtifacts(
                rpm=RpmTarget(enabled=True, directories=[Directory(path="/var/lib/x_exp")])
            ),
        ),
    )
    out = work / "x_exp-1.0.0-1.el9.x86_64.rpm"
    NfpmPackager(_WritingRunner(out)).package(
        manifest,
        packager="rpm",
        target="el9",
        arch="amd64",
        binary_src=_binary(tmp_path),
        work_dir=work,
    )
    cfg = yaml.safe_load((work / "nfpm.yaml").read_text(encoding="utf-8"))
    assert any(c.get("type") == "dir" and c["dst"] == "/var/lib/x_exp" for c in cfg["contents"])


def test_package_missing_target_raises(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    manifest = ExporterManifest(
        kind="exporter",
        name="x_exp",
        description="d",
        version="1.0.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="o/r"),
            build=Build(method="binary_repack", binary_name="x_exp"),
            artifacts=ExporterArtifacts(rpm=RpmTarget(enabled=True)),
        ),
    )
    with pytest.raises(BuildError, match="no deb target"):
        NfpmPackager(FakeRunner()).package(
            manifest,
            packager="deb",
            target="ubuntu-24.04",
            arch="amd64",
            binary_src=_binary(tmp_path),
            work_dir=work,
        )


def test_package_raises_when_nfpm_produces_nothing(
    manifest: ExporterManifest, tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    # FakeRunner returns rc=0 but writes no package; the post-build glob is empty.
    with pytest.raises(BuildError, match="produced no"):
        NfpmPackager(FakeRunner()).package(
            manifest,
            packager="rpm",
            target="el9",
            arch="amd64",
            binary_src=_binary(tmp_path),
            work_dir=work,
        )


@pytest.mark.skipif(shutil.which("nfpm") is None, reason="nfpm not installed")
def test_real_nfpm_builds_an_rpm(manifest: ExporterManifest, tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    # Stage the extra-file source nfpm reads (relative to its cwd=work_dir).
    # Sourcing real extra files from the exporter tree is the SP1.4 producer's
    # job; here we only need a file on disk so the POC exercises nfpm fully.
    (work / "assets").mkdir()
    (work / "assets" / "node.conf").write_text("# node_exporter config\n", encoding="utf-8")
    artifact = NfpmPackager(SubprocessRunner()).package(
        manifest,
        packager="rpm",
        target="el9",
        arch="amd64",
        binary_src=_binary(tmp_path),
        work_dir=work,
    )
    produced = list(work.glob("*.rpm"))
    assert produced, "nfpm did not produce an rpm"
    assert artifact.sha256 == file_sha256(produced[0])
