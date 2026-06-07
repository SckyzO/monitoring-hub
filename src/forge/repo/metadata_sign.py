"""Repository metadata signing (spec §5.3).

Distinct from package signing (``packaging/sign.py`` signs ``.rpm``/``.deb``);
this signs the repo *metadata* — detached/armored for ``repomd.xml``. The
passphrase flows through gpg-agent / the environment, **never argv** (the
May-2026 secrets rule: nothing sensitive in ``ps``/history). The ``key_id`` is
not secret.
"""

from __future__ import annotations

from pathlib import Path

from forge.domain.errors import SigningError
from forge.packaging.runner import CommandRunner


def sign_repomd(repomd: Path, *, key_id: str, runner: CommandRunner) -> Path:
    """Detached-sign ``repomd.xml`` → ``repomd.xml.asc`` (returned)."""
    signature = repomd.with_name(repomd.name + ".asc")
    result = runner.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--detach-sign",
            "--armor",
            "-u",
            key_id,
            "--output",
            str(signature),
            str(repomd),
        ]
    )
    if result.returncode != 0:
        raise SigningError(f"signing {repomd.name} failed: {result.stderr}")
    return signature
