"""GPG signing adapter: rpmsign / debsigs, secrets via env never argv."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from forge.domain.errors import SigningError
from forge.packaging.runner import CommandResult
from forge.packaging.sign import GpgSigner
from tests.packaging.conftest import FakeRunner


def test_sign_rpm_invokes_rpmsign_with_key(tmp_path: Path) -> None:
    pkg = tmp_path / "node_exporter-1.9.1-1.el9.x86_64.rpm"
    pkg.write_bytes(b"rpm")
    runner = FakeRunner()
    GpgSigner(runner).sign(pkg, packager="rpm", key_id="ABCD1234")
    args = cast("list[str]", runner.calls[0]["args"])
    assert "rpmsign" in args[0] or args[0] == "rpm"
    assert "--addsign" in args
    assert str(pkg) in args
    assert "ABCD1234" in " ".join(args)


def test_sign_deb_invokes_debsigs(tmp_path: Path) -> None:
    pkg = tmp_path / "node-exporter_1.9.1_amd64.deb"
    pkg.write_bytes(b"deb")
    runner = FakeRunner()
    GpgSigner(runner).sign(pkg, packager="deb", key_id="ABCD1234")
    args = cast("list[str]", runner.calls[0]["args"])
    assert args[0] == "debsigs"
    assert str(pkg) in args


def test_passphrase_is_never_in_argv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GPG_PASSPHRASE", "s3cret-do-not-leak")
    pkg = tmp_path / "x.rpm"
    pkg.write_bytes(b"rpm")
    runner = FakeRunner()
    GpgSigner(runner).sign(pkg, packager="rpm", key_id="ABCD1234")
    for call in runner.calls:
        args = cast("list[str]", call["args"])
        assert "s3cret-do-not-leak" not in " ".join(args)


def test_sign_raises_signing_error_on_failure(tmp_path: Path) -> None:
    pkg = tmp_path / "x.rpm"
    pkg.write_bytes(b"rpm")
    runner = FakeRunner(
        [CommandResult(args=["rpmsign"], returncode=1, stdout="", stderr="bad key")]
    )
    with pytest.raises(SigningError, match="bad key"):
        GpgSigner(runner).sign(pkg, packager="rpm", key_id="ABCD1234")
