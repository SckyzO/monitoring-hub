"""L2 smoke (gated): real createrepo_c/mergerepo_c prove a one-item bump keeps the
rest. Skipped unless MH_SMOKE=1 and the tools are on PATH (CI container)."""

from __future__ import annotations

import gzip
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from forge.packaging.runner import SubprocessRunner
from forge.repo.rpm import build_rpm_repo, merge_rpm_repo

pytestmark = pytest.mark.skipif(
    os.environ.get("MH_SMOKE") != "1"
    or shutil.which("createrepo_c") is None
    or shutil.which("mergerepo_c") is None
    or shutil.which("nfpm") is None
    or shutil.which("zstd") is None,
    reason="gated: needs MH_SMOKE=1 + createrepo_c/mergerepo_c/nfpm/zstd",
)

_PREFIX = "https://example/rpm-el9-x86_64/"


def _primary_text(repodata: Path) -> str:
    """Decode the primary metadata regardless of createrepo_c's compressor.

    createrepo_c >= 1.x defaults to zstd (``*primary.xml.zst``); older builds
    emit gzip (``*primary.xml.gz``). Pick whichever is present and decompress it.
    """
    primary = next(repodata.glob("*primary.xml.*"))
    if primary.suffix == ".gz":
        return gzip.decompress(primary.read_bytes()).decode()
    return subprocess.run(
        ["zstd", "-dc", str(primary)], check=True, capture_output=True
    ).stdout.decode()


def _rpm(d: Path, name: str, version: str) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    cfg = d / "c.yaml"
    cfg.write_text(
        f"name: {name}\narch: amd64\nversion: {version}\n"
        f"maintainer: x <x@x>\ndescription: s\n"
        f"contents:\n  - src: /etc/hostname\n    dst: /opt/{name}/m\n"
    )
    subprocess.run(["nfpm", "package", "-f", str(cfg), "-p", "rpm", "-t", str(d)], check=True)
    return next(d.glob(f"{name}-{version}*.rpm"))


def _names(repodata: Path) -> set[str]:
    return set(re.findall(r"<name>([^<]+)</name>", _primary_text(repodata)))


def test_one_item_bump_keeps_the_others(tmp_path: Path) -> None:
    runner = SubprocessRunner()
    src = tmp_path / "src"
    n1 = _rpm(src, "node_exporter", "1.0.0")
    m1 = _rpm(src, "mysqld_exporter", "1.0.0")
    published = tmp_path / "published"
    build_rpm_repo(
        packages=[n1, m1],
        repodata_dir=published / "repodata",
        location_prefix=_PREFIX,
        runner=runner,
    )
    assert _names(published / "repodata") == {"node_exporter", "mysqld_exporter"}

    n2 = _rpm(tmp_path / "new", "node_exporter", "2.0.0")
    out = tmp_path / "out" / "repodata"
    merge_rpm_repo(
        new_package=n2,
        published_parent=published,
        repodata_dir=out,
        location_prefix=_PREFIX,
        runner=runner,
    )
    assert _names(out) == {"node_exporter", "mysqld_exporter"}  # mysqld preserved
    text = _primary_text(out)
    assert "2.0.0" in text and "node_exporter-1.0.0" not in text
