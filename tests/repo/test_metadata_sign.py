"""Repo metadata signing: detached-sign repomd.xml, secrets never in argv."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.domain.errors import SigningError
from forge.packaging.runner import CommandResult
from forge.repo.metadata_sign import sign_repomd
from tests.packaging.conftest import FakeRunner


def _repomd(tmp_path: Path) -> Path:
    repomd = tmp_path / "repodata" / "repomd.xml"
    repomd.parent.mkdir(parents=True)
    repomd.write_text("<repomd/>")
    return repomd


def test_sign_repomd_emits_detached_armored_signature(tmp_path: Path) -> None:
    repomd = _repomd(tmp_path)
    runner = FakeRunner()
    sig = sign_repomd(repomd, key_id="ABCD1234", runner=runner)
    assert sig == repomd.with_name("repomd.xml.asc")
    args = cast("list[str]", runner.calls[0]["args"])
    assert args[0] == "gpg"
    assert "--detach-sign" in args
    assert "--armor" in args
    assert "ABCD1234" in args
    assert str(repomd) in args


def test_sign_repomd_never_puts_passphrase_in_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GPG_PASSPHRASE", "s3cret-do-not-leak")
    repomd = _repomd(tmp_path)
    runner = FakeRunner()
    sign_repomd(repomd, key_id="ABCD1234", runner=runner)
    for call in runner.calls:
        args = cast("list[str]", call["args"])
        assert "s3cret-do-not-leak" not in " ".join(args)


def test_sign_repomd_raises_signing_error_on_failure(tmp_path: Path) -> None:
    repomd = _repomd(tmp_path)
    runner = FakeRunner(
        [CommandResult(args=["gpg"], returncode=2, stdout="", stderr="no secret key")]
    )
    with pytest.raises(SigningError, match="no secret key"):
        sign_repomd(repomd, key_id="ABCD1234", runner=runner)
