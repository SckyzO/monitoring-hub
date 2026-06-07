"""GPG signing adapter (spec §7.1, §14).

Secrets (passphrase) flow through the environment / gpg-agent, **never argv**
(matches the May-2026 security fix: nothing sensitive in ``ps``/history). The
``key_id`` is not secret. RPM uses ``rpmsign --addsign``; DEB uses ``debsigs``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from forge.domain.errors import SigningError
from forge.packaging.runner import CommandRunner


class GpgSigner:
    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner

    def sign(self, path: Path, *, packager: Literal["rpm", "deb"], key_id: str) -> None:
        if packager == "rpm":
            args = ["rpmsign", "--define", f"_gpg_name {key_id}", "--addsign", str(path)]
        else:
            args = ["debsigs", "--sign=origin", f"--default-key={key_id}", str(path)]

        result = self._runner.run(args)
        if result.returncode != 0:
            raise SigningError(f"signing {path.name} failed: {result.stderr}")
