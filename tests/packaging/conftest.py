"""Shared fixtures for packaging tests: an in-memory FakeRunner that records
calls and returns scripted results. The exporter ``manifest`` fixture lives in
the project-wide ``tests/conftest.py`` (shared with the kinds tests)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from forge.packaging.runner import CommandResult


class FakeRunner:
    """Records every ``run`` call; returns a queued result (default rc=0)."""

    def __init__(self, results: list[CommandResult] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self._results = list(results or [])

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        arg_list = list(args)
        self.calls.append(
            {"args": arg_list, "cwd": cwd, "env": dict(env) if env else None, "stdin": stdin}
        )
        if self._results:
            return self._results.pop(0)
        return CommandResult(args=arg_list, returncode=0, stdout="", stderr="")
