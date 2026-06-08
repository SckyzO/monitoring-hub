"""L3 distribution smoke (spec §9.3): assemble a real SIGNED repo and install
from it on the target distro with signature verification ON.

Gated by FORGE_DOCKER_TESTS=1; needs nfpm + docker + createrepo_c + apt-ftparchive
+ gpg + network. Runs OUTSIDE ``make ci`` (forge-smoke.yml), like the SP1 L3.
Metadata is signed (not the .rpm), so RPM uses repo_gpgcheck; APT uses signed-by.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404 — driving host docker/gpg is the point
from pathlib import Path

import pytest

from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.manifest import (
    Build,
    DebTarget,
    DockerTarget,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    RpmTarget,
    Systemd,
    Upstream,
)
from forge.fetch.http import HttpxDownloader
from forge.kinds.base import BuildContext
from forge.kinds.exporter import ExporterProducer
from forge.packaging.runner import SubprocessRunner
from forge.repo.builder import build_distribution

pytestmark = pytest.mark.skipif(
    os.environ.get("FORGE_DOCKER_TESTS") != "1"
    or any(
        shutil.which(t) is None for t in ("nfpm", "docker", "createrepo_c", "apt-ftparchive", "gpg")
    ),
    reason="set FORGE_DOCKER_TESTS=1 with nfpm+docker+createrepo_c+apt-ftparchive+gpg",
)

_VERSION = "v1.9.1"
_CLEAN = "1.9.1"


def _manifest() -> ExporterManifest:
    return ExporterManifest(
        kind="exporter",
        name="node_exporter",
        description="Prometheus exporter for hardware and OS metrics",
        category="System",
        version=_VERSION,
        license="Apache-2.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="prometheus/node_exporter"),
            build=Build(method="binary_repack", binary_name="node_exporter", archs=["amd64"]),
            artifacts=ExporterArtifacts(
                rpm=RpmTarget(
                    enabled=True,
                    targets=["el9"],
                    summary="Node exporter",
                    systemd=Systemd(enabled=True),
                    system_user="prometheus",
                ),
                deb=DebTarget(
                    enabled=True,
                    targets=["ubuntu-24.04"],
                    systemd=Systemd(enabled=True),
                    system_user="prometheus",
                ),
                docker=DockerTarget(enabled=False),
            ),
        ),
    )


def _catalog() -> Catalog:
    return Catalog(
        generated_at="2026-06-08T00:00:00Z",
        items=[
            CatalogEntry(
                kind="exporter",
                name="node_exporter",
                version=_CLEAN,
                category="System",
                description="Node exporter",
                artifacts=[
                    Artifact(type="rpm", target="el9", arch="amd64", sha256="0" * 64),
                    Artifact(type="deb", target="ubuntu-24.04", arch="amd64", sha256="0" * 64),
                ],
            )
        ],
    )


def _gen_key(gnupg: Path) -> tuple[str, Path]:
    """Generate an ephemeral, passphrase-less GPG key; return (key_id, public.asc)."""
    gnupg.mkdir(mode=0o700, exist_ok=True)
    params = gnupg / "params"
    params.write_text(
        "Key-Type: eddsa\nKey-Curve: ed25519\n"
        "Name-Real: monitoring-hub-smoke\nName-Email: smoke@example.com\n"
        "Expire-Date: 0\n%no-protection\n%commit\n",
        encoding="utf-8",
    )
    env = {**os.environ, "GNUPGHOME": str(gnupg)}
    subprocess.run(  # noqa: S603
        ["gpg", "--batch", "--gen-key", str(params)], env=env, check=True, capture_output=True
    )
    listing = subprocess.run(  # noqa: S603
        ["gpg", "--list-keys", "--with-colons"],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    key_id = next(ln.split(":")[4] for ln in listing.stdout.splitlines() if ln.startswith("pub"))
    pub = gnupg / "public.asc"
    pub.write_text(
        subprocess.run(  # noqa: S603
            ["gpg", "--armor", "--export", key_id],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout,
        encoding="utf-8",
    )
    return key_id, pub


def _build_signed_tree(tmp_path: Path) -> Path:
    """Build pkgs + a signed file:// repo; return the tree root mounted at /repo."""
    pkgs = tmp_path / "dist"
    ctx = BuildContext(work_dir=pkgs, downloader=HttpxDownloader(), runner=SubprocessRunner())
    ExporterProducer().build(_manifest(), ctx)

    gnupg = tmp_path / "gnupg"
    key_id, pub = _gen_key(gnupg)

    tree = tmp_path / "tree"
    public, release = tree / "public", tree / "release"
    os.environ["GNUPGHOME"] = str(gnupg)  # real gpg signing inside build_distribution
    build_distribution(
        catalog=_catalog(),
        packages_dir=pkgs,
        dashboards_dir=tmp_path / "none",
        public_out=public,
        release_out=release,
        package_base_url="file:///repo/release",
        pages_base_url="file:///repo/public",
        key_id=key_id,
        public_key=pub,
        runner=SubprocessRunner(),
    )
    return tree


def _docker_run(image: str, tree: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            "linux/amd64",
            "-v",
            f"{tree}:/repo:ro",
            image,
            "bash",
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )


def test_el9_rpm_consumes_signed_repo(tmp_path: Path) -> None:
    tree = _build_signed_tree(tmp_path)
    script = (
        "set -e; rpm --import /repo/public/RPM-GPG-KEY-monitoring-hub; "
        "printf '[mh]\\nname=mh\\nbaseurl=file:///repo/public/el9/x86_64\\n"
        "enabled=1\\ngpgcheck=0\\nrepo_gpgcheck=1\\n"
        "gpgkey=file:///repo/public/RPM-GPG-KEY-monitoring-hub\\n' "
        "> /etc/yum.repos.d/mh.repo; "
        "dnf -y install node_exporter; node_exporter --version"
    )
    result = _docker_run("almalinux:9", tree, script)
    assert result.returncode == 0, result.stderr
    assert "node_exporter" in result.stdout + result.stderr


def test_ubuntu2404_deb_consumes_signed_repo(tmp_path: Path) -> None:
    tree = _build_signed_tree(tmp_path)
    script = (
        "set -e; install -d /etc/apt/keyrings; "
        "cp /repo/public/apt/monitoring-hub.asc /etc/apt/keyrings/mh.asc; "
        "echo 'deb [signed-by=/etc/apt/keyrings/mh.asc] file:///repo/release/apt-noble ./' "
        "> /etc/apt/sources.list.d/mh.list; "
        "apt-get update; apt-get install -y node-exporter; node_exporter --version"
    )
    result = _docker_run("ubuntu:24.04", tree, script)
    assert result.returncode == 0, result.stderr
    assert "node_exporter" in result.stdout + result.stderr
