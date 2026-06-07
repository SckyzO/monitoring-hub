"""Repo metadata signing: detached-sign repomd.xml, secrets never in argv."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.domain.errors import SigningError
from forge.packaging.runner import CommandResult
from forge.repo.metadata_sign import sign_apt_release, sign_repomd
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


def _release(tmp_path: Path) -> Path:
    release = tmp_path / "apt-noble" / "Release"
    release.parent.mkdir(parents=True)
    release.write_text("Origin: monitoring-hub\n")
    return release


def test_sign_apt_release_emits_inrelease_and_release_gpg(tmp_path: Path) -> None:
    release = _release(tmp_path)
    runner = FakeRunner()
    inrelease, release_gpg = sign_apt_release(release, key_id="ABCD1234", runner=runner)
    assert inrelease == release.with_name("InRelease")
    assert release_gpg == release.with_name("Release.gpg")

    clearsign = cast("list[str]", runner.calls[0]["args"])
    assert clearsign[0] == "gpg"
    assert "--clearsign" in clearsign
    assert "ABCD1234" in clearsign
    assert str(release) in clearsign

    detach = cast("list[str]", runner.calls[1]["args"])
    assert "--detach-sign" in detach
    assert "--armor" in detach
    assert "ABCD1234" in detach


def test_sign_apt_release_never_puts_passphrase_in_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GPG_PASSPHRASE", "s3cret-do-not-leak")
    release = _release(tmp_path)
    runner = FakeRunner()
    sign_apt_release(release, key_id="ABCD1234", runner=runner)
    for call in runner.calls:
        args = cast("list[str]", call["args"])
        assert "s3cret-do-not-leak" not in " ".join(args)


def test_sign_apt_release_raises_on_clearsign_failure(tmp_path: Path) -> None:
    release = _release(tmp_path)
    runner = FakeRunner(
        [CommandResult(args=["gpg"], returncode=2, stdout="", stderr="no secret key")]
    )
    with pytest.raises(SigningError, match="no secret key"):
        sign_apt_release(release, key_id="ABCD1234", runner=runner)


def test_sign_apt_release_raises_on_detach_failure(tmp_path: Path) -> None:
    release = _release(tmp_path)
    runner = FakeRunner(
        [
            CommandResult(args=["gpg"], returncode=0, stdout="", stderr=""),
            CommandResult(args=["gpg"], returncode=2, stdout="", stderr="detach boom"),
        ]
    )
    with pytest.raises(SigningError, match="detach boom"):
        sign_apt_release(release, key_id="ABCD1234", runner=runner)
