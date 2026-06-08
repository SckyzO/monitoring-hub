"""archive.pack: tar the assembled bundle tree into a .tar.gz (spec §5.5)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.bundle.archive import pack
from forge.domain.errors import BundleError
from forge.packaging.runner import CommandResult
from tests.packaging.conftest import FakeRunner


def test_pack_runs_literal_tar_argv(tmp_path: Path) -> None:
    staging = tmp_path / "tree"
    staging.mkdir()
    out = tmp_path / "bundle.tar.gz"
    runner = FakeRunner()

    result = pack(staging, out, runner=runner)

    assert result == out
    assert len(runner.calls) == 1
    assert cast("list[str]", runner.calls[0]["args"]) == [
        "tar",
        "-czf",
        str(out),
        "-C",
        str(staging),
        ".",
    ]


def test_pack_nonzero_raises_bundle_error(tmp_path: Path) -> None:
    staging = tmp_path / "tree"
    staging.mkdir()
    runner = FakeRunner([CommandResult(args=["tar"], returncode=2, stdout="", stderr="boom")])

    with pytest.raises(BundleError, match="tar failed"):
        pack(staging, tmp_path / "b.tar.gz", runner=runner)
