"""CommandRunner protocol + SubprocessRunner (the single I/O seam)."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.domain.errors import CommandError
from forge.packaging.runner import CommandResult, CommandRunner, SubprocessRunner


def test_subprocess_runner_satisfies_protocol() -> None:
    assert isinstance(SubprocessRunner(), CommandRunner)


def test_run_captures_stdout_and_zero_return() -> None:
    result = SubprocessRunner().run(["printf", "hello"])
    assert isinstance(result, CommandResult)
    assert result.returncode == 0
    assert result.stdout == "hello"
    assert result.args == ["printf", "hello"]


def test_run_does_not_raise_on_nonzero_exit() -> None:
    result = SubprocessRunner().run(["sh", "-c", "exit 3"])
    assert result.returncode == 3


def test_run_passes_stdin() -> None:
    result = SubprocessRunner().run(["cat"], stdin="piped")
    assert result.stdout == "piped"


def test_run_uses_cwd(tmp_path: Path) -> None:
    (tmp_path / "marker").write_text("x")
    result = SubprocessRunner().run(["ls"], cwd=tmp_path)
    assert "marker" in result.stdout


def test_missing_executable_raises_command_error() -> None:
    with pytest.raises(CommandError, match="forge-no-such-bin"):
        SubprocessRunner().run(["forge-no-such-bin"])
