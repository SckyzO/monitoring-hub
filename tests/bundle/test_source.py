"""Artefact sources: local tree + published Releases/Pages (spec §5.3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.bundle.resolver import ResolvedArtifact
from forge.bundle.source import LocalDirSource
from forge.domain.artifact import Artifact
from forge.domain.errors import BundleError


def _rpm() -> ResolvedArtifact:
    return ResolvedArtifact(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        artifact=Artifact(type="rpm", target="el9", arch="amd64", sha256="a"),
        filename="node_exporter-1.9.1-1.el9.x86_64.rpm",
    )


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
