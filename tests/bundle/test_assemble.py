"""assemble_bundle: arrange fetched artefacts into the bundle tree (spec §5.4/§6)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import pytest

from forge.bundle.assemble import assemble_bundle
from forge.bundle.resolver import ResolvedArtifact
from forge.domain.artifact import Artifact
from forge.domain.errors import BundleError
from forge.domain.recipe import BundleRecipe, RecipeItem
from tests.packaging.conftest import FakeRunner

_RPM = "node_exporter-1.9.1-1.el9.x86_64.rpm"
_DEB = "node-exporter_1.9.1-1_amd64.deb"
_DASH = "node-overview.json"


def _resolved() -> list[ResolvedArtifact]:
    return [
        ResolvedArtifact(
            kind="exporter",
            name="node_exporter",
            version="1.9.1",
            artifact=Artifact(type="rpm", target="el9", arch="amd64", sha256="a"),
            filename=_RPM,
        ),
        ResolvedArtifact(
            kind="exporter",
            name="node_exporter",
            version="1.9.1",
            artifact=Artifact(type="deb", target="ubuntu-24.04", arch="amd64", sha256="b"),
            filename=_DEB,
        ),
        ResolvedArtifact(
            kind="dashboard",
            name="node-overview",
            version="39",
            artifact=Artifact(type="grafana-dashboard", sha256="c"),
            filename=_DASH,
        ),
    ]


def _inputs(tmp_path: Path) -> Path:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / _RPM).write_text("RPM", encoding="utf-8")
    (inputs / _DEB).write_text("DEB", encoding="utf-8")
    (inputs / _DASH).write_text('{"title": "n"}', encoding="utf-8")
    return inputs


def _recipe() -> BundleRecipe:
    return BundleRecipe(
        generated_at="2026-06-08T00:00:00Z",
        items=[RecipeItem(kind="exporter", name="node_exporter", version="1.9.1")],
    )


def test_assemble_unsigned_layout(tmp_path: Path) -> None:
    staging = tmp_path / "bundle"
    assemble_bundle(
        _resolved(),
        inputs_dir=_inputs(tmp_path),
        staging=staging,
        recipe=_recipe(),
        runner=FakeRunner(),
    )
    assert (staging / "yum" / "el9" / "x86_64" / _RPM).is_file()
    assert (staging / "apt" / "noble" / _DEB).is_file()
    assert (staging / "apt" / "noble" / "Release").is_file()
    assert (staging / "dashboards" / _DASH).is_file()
    assert (staging / "recipe.json").is_file()
    assert (staging / "README.md").is_file()
    assert (staging / "SHA256SUMS").is_file()
    # unsigned → no detached signatures, no key file
    assert not (staging / "recipe.json.asc").exists()
    assert not (staging / "RPM-GPG-KEY-monitoring-hub").exists()


def test_assemble_sha256sums_covers_files(tmp_path: Path) -> None:
    staging = tmp_path / "bundle"
    assemble_bundle(
        _resolved(),
        inputs_dir=_inputs(tmp_path),
        staging=staging,
        recipe=_recipe(),
        runner=FakeRunner(),
    )
    lines = (staging / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    rels = {line.split("  ", 1)[1] for line in lines}
    assert "recipe.json" in rels
    assert "README.md" in rels
    assert f"yum/el9/x86_64/{_RPM}" in rels
    assert f"dashboards/{_DASH}" in rels
    assert "SHA256SUMS" not in rels  # never lists itself
    assert all(re.fullmatch(r"[0-9a-f]{64}", line.split("  ", 1)[0]) for line in lines)


def test_assemble_readme_unsigned_has_no_import(tmp_path: Path) -> None:
    staging = tmp_path / "bundle"
    assemble_bundle(
        _resolved(),
        inputs_dir=_inputs(tmp_path),
        staging=staging,
        recipe=_recipe(),
        runner=FakeRunner(),
    )
    readme = (staging / "README.md").read_text(encoding="utf-8")
    assert "repo_gpgcheck=0" in readme
    assert "rpm --import" not in readme
    assert "file://$PWD/yum/el9/x86_64" in readme
    assert "file://$PWD/apt/noble" in readme


def test_assemble_signed_invokes_gpg_and_key(tmp_path: Path) -> None:
    staging = tmp_path / "bundle"
    pubkey = tmp_path / "key.asc"
    pubkey.write_text("PUB", encoding="utf-8")
    runner = FakeRunner()
    assemble_bundle(
        _resolved(),
        inputs_dir=_inputs(tmp_path),
        staging=staging,
        recipe=_recipe(),
        key_id="KID",
        public_key=pubkey,
        runner=runner,
    )
    all_args = [cast("list[str]", c["args"]) for c in runner.calls]
    gpg_calls = [a for a in all_args if a[0] == "gpg"]
    # repomd detach + apt clearsign + apt detach + recipe detach = 4 gpg invocations
    assert len(gpg_calls) == 4
    for args in gpg_calls:
        assert "KID" in args
        assert "PASS" not in " ".join(args)  # passphrase never in argv
    assert (staging / "RPM-GPG-KEY-monitoring-hub").read_text(encoding="utf-8") == "PUB"
    readme = (staging / "README.md").read_text(encoding="utf-8")
    assert "rpm --import" in readme
    assert "repo_gpgcheck=1" in readme


def test_assemble_missing_blob_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(BundleError, match="not found"):
        assemble_bundle(
            _resolved(),
            inputs_dir=empty,
            staging=tmp_path / "bundle",
            recipe=_recipe(),
            runner=FakeRunner(),
        )


def test_assemble_idempotent_excludes_prior_sha256sums(tmp_path: Path) -> None:
    staging = tmp_path / "bundle"
    inputs = _inputs(tmp_path)
    for _ in range(2):
        assemble_bundle(
            _resolved(),
            inputs_dir=inputs,
            staging=staging,
            recipe=_recipe(),
            runner=FakeRunner(),
        )
    rels = {
        line.split("  ", 1)[1]
        for line in (staging / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    }
    assert "SHA256SUMS" not in rels
