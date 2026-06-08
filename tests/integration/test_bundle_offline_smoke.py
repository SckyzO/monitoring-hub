"""L3 offline smoke (spec §9.3): bundle real rpm/deb, extract in a --network none
container, configure a file:// repo from the bundle, install, run the binary.

Gated by FORGE_DOCKER_TESTS=1; needs nfpm + docker + createrepo_c + apt-ftparchive
+ gpg + tar. Proves the bundle installs with ZERO network and that the co-located
relative-href yum repo resolves offline. Signed variants add repo_gpgcheck /
signed-by verification.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404 — driving host docker/gpg is the point
from pathlib import Path

import pytest

from forge.bundle.builder import build_bundle
from forge.bundle.resolver import recipe_from_selection
from forge.bundle.source import LocalDirSource
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

pytestmark = pytest.mark.skipif(
    os.environ.get("FORGE_DOCKER_TESTS") != "1"
    or any(
        shutil.which(t) is None
        for t in ("nfpm", "docker", "createrepo_c", "apt-ftparchive", "gpg", "tar")
    ),
    reason="set FORGE_DOCKER_TESTS=1 with nfpm+docker+createrepo_c+apt-ftparchive+gpg+tar",
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
    gnupg.mkdir(mode=0o700, exist_ok=True)
    params = gnupg / "params"
    params.write_text(
        "Key-Type: eddsa\nKey-Curve: ed25519\n"
        "Name-Real: mh-offline-smoke\nName-Email: smoke@example.com\n"
        "Expire-Date: 0\n%no-protection\n%commit\n",
        encoding="utf-8",
    )
    env = {**os.environ, "GNUPGHOME": str(gnupg)}
    subprocess.run(  # noqa: S603
        ["gpg", "--batch", "--gen-key", str(params)], env=env, check=True, capture_output=True
    )
    listing = subprocess.run(  # noqa: S603
        ["gpg", "--list-keys", "--with-colons"], env=env, check=True, capture_output=True, text=True
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


def _make_bundle(tmp_path: Path, *, sign: bool) -> Path:
    """Build real rpm+deb, then bundle them with LocalDirSource. Returns the archive."""
    pkgs = tmp_path / "dist"
    ctx = BuildContext(work_dir=pkgs, downloader=HttpxDownloader(), runner=SubprocessRunner())
    ExporterProducer().build(_manifest(), ctx)

    key_id: str | None = None
    public_key: Path | None = None
    if sign:
        key_id, public_key = _gen_key(tmp_path / "gnupg")
        os.environ["GNUPGHOME"] = str(tmp_path / "gnupg")

    recipe = recipe_from_selection(["node_exporter"], _catalog(), targets=None, arches=["amd64"])
    out = tmp_path / "bundle.tar.gz"
    build_bundle(
        recipe=recipe,
        catalog=_catalog(),
        source=LocalDirSource(pkgs),
        staging=tmp_path / "work",
        out=out,
        key_id=key_id,
        public_key=public_key,
        runner=SubprocessRunner(),
    )
    return out


def _docker_offline(image: str, bundle: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--platform",
            "linux/amd64",
            "-v",
            f"{bundle}:/bundle.tar.gz:ro",
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


_RPM_INSTALL = (
    "set -e; mkdir /b; tar xzf /bundle.tar.gz -C /b; cd /b; "
    "{import_key}"
    "printf '[mh]\\nname=mh\\nbaseurl=file:///b/yum/el9/x86_64\\n"
    "enabled=1\\ngpgcheck=0\\nrepo_gpgcheck={repo_gpgcheck}\\n{gpgkey}' "
    "> /etc/yum.repos.d/mh.repo; "
    # air-gapped: only the bundle repo is reachable; dnf must not touch the
    # distro defaults (mirrors.almalinux.org) which cannot resolve under --network none
    "dnf -y --disablerepo='*' --enablerepo=mh install node_exporter; node_exporter --version"
)

_DEB_INSTALL = (
    "set -e; mkdir /b; tar xzf /bundle.tar.gz -C /b; cd /b; "
    "{keyring}"
    "echo 'deb [{signed_by}] file:///b/apt/noble ./' > /etc/apt/sources.list.d/mh.list; "
    "apt-get update; apt-get install -y node-exporter; node_exporter --version"
)


@pytest.mark.parametrize("sign", [False, True])
def test_el9_rpm_installs_offline(tmp_path: Path, sign: bool) -> None:
    bundle = _make_bundle(tmp_path, sign=sign)
    script = _RPM_INSTALL.format(
        import_key="rpm --import /b/RPM-GPG-KEY-monitoring-hub; " if sign else "",
        repo_gpgcheck=1 if sign else 0,
        gpgkey="gpgkey=file:///b/RPM-GPG-KEY-monitoring-hub\\n" if sign else "",
    )
    result = _docker_offline("almalinux:9", bundle, script)
    assert result.returncode == 0, result.stderr
    assert "node_exporter" in result.stdout + result.stderr


@pytest.mark.parametrize("sign", [False, True])
def test_ubuntu2404_deb_installs_offline(tmp_path: Path, sign: bool) -> None:
    bundle = _make_bundle(tmp_path, sign=sign)
    script = _DEB_INSTALL.format(
        keyring=(
            "install -d /etc/apt/keyrings; "
            "cp /b/RPM-GPG-KEY-monitoring-hub /etc/apt/keyrings/mh.asc; "
            if sign
            else ""
        ),
        signed_by="signed-by=/etc/apt/keyrings/mh.asc" if sign else "trusted=yes",
    )
    result = _docker_offline("ubuntu:24.04", bundle, script)
    assert result.returncode == 0, result.stderr
    assert "node_exporter" in result.stdout + result.stderr
