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


def sign_detached(path: Path, *, key_id: str, runner: CommandRunner) -> Path:
    """Detached-armored-sign ``path`` → ``path.asc`` (returned).

    Generic over what is signed (``repomd.xml``, ``recipe.json``, …); the
    passphrase flows through gpg-agent/env, never argv.
    """
    signature = path.with_name(path.name + ".asc")
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
            str(path),
        ]
    )
    if result.returncode != 0:
        raise SigningError(f"signing {path.name} failed: {result.stderr}")
    return signature


def sign_repomd(repomd: Path, *, key_id: str, runner: CommandRunner) -> Path:
    """Detached-sign ``repomd.xml`` → ``repomd.xml.asc`` (returned)."""
    return sign_detached(repomd, key_id=key_id, runner=runner)


def sign_apt_release(release: Path, *, key_id: str, runner: CommandRunner) -> tuple[Path, Path]:
    """Sign a flat ``Release`` → ``(InRelease, Release.gpg)`` (both returned)."""
    inrelease = release.with_name("InRelease")
    release_gpg = release.with_name("Release.gpg")

    clearsign = runner.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--clearsign",
            "-u",
            key_id,
            "--output",
            str(inrelease),
            str(release),
        ]
    )
    if clearsign.returncode != 0:
        raise SigningError(f"clearsigning {release.name} failed: {clearsign.stderr}")

    detached = runner.run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--detach-sign",
            "--armor",
            "-u",
            key_id,
            "--output",
            str(release_gpg),
            str(release),
        ]
    )
    if detached.returncode != 0:
        raise SigningError(f"detach-signing {release.name} failed: {detached.stderr}")

    return inrelease, release_gpg
