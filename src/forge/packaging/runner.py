"""Command execution seam (spec §15).

``CommandRunner`` is the single I/O boundary for the packaging adapters: the
real ``SubprocessRunner`` shells out; tests inject a fake. A non-zero exit is
**not** an error here — it is returned in ``CommandResult`` so the calling
adapter wraps it in the right domain error. Only a failure to *launch* the
process (missing binary) raises ``CommandError``.
"""

from __future__ import annotations

# Controlled list args, shell=False, no user-controlled executable name (see run()).
import subprocess  # nosec B404
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from forge.domain.errors import CommandError


class CommandResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    args: list[str]
    returncode: int
    stdout: str
    stderr: str


@runtime_checkable
class CommandRunner(Protocol):
    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult: ...


class SubprocessRunner:
    """Real runner: ``subprocess.run`` with ``shell=False`` and list args."""

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        arg_list = list(args)
        try:
            # list args, shell=False, no user-controlled executable name.
            completed = subprocess.run(  # nosec B603
                arg_list,
                cwd=cwd,
                env=dict(env) if env is not None else None,
                input=stdin,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise CommandError(f"cannot run {arg_list[0]!r}: {exc}") from exc
        return CommandResult(
            args=arg_list,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
