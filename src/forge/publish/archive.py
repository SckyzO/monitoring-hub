"""Per-app archive releases (spec §4.4): mirror each version to its own release
``{name}-v{version}`` for visibility + manual downgrade, keeping the newest N.

Retention orders ``{name}-v*`` by ``gh release list`` (newest first) and deletes
beyond ``keep`` — no semver parsing, robust to odd upstream tags.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from forge.domain.errors import PublishError
from forge.packaging.runner import CommandRunner

_NOTES = "monitoring-hub per-version archive"


class ArchiveReleasesPublisher:
    def __init__(self, *, repo: str, runner: CommandRunner, keep: int = 10) -> None:
        self._repo = repo
        self._runner = runner
        self._keep = keep

    def publish_item(self, *, name: str, version: str, assets: Sequence[Path]) -> None:
        tag = f"{name}-v{version}"
        if self._runner.run(["gh", "release", "view", tag, "--repo", self._repo]).returncode != 0:
            self._run(
                [
                    "gh",
                    "release",
                    "create",
                    tag,
                    "--repo",
                    self._repo,
                    "--title",
                    tag,
                    "--notes",
                    _NOTES,
                ]
            )
        if assets:
            self._run(
                [
                    "gh",
                    "release",
                    "upload",
                    tag,
                    *(str(a) for a in assets),
                    "--clobber",
                    "--repo",
                    self._repo,
                ]
            )
        self.enforce_retention(name)

    def enforce_retention(self, name: str) -> None:
        listing = self._runner.run(
            [
                "gh",
                "release",
                "list",
                "--repo",
                self._repo,
                "--limit",
                "1000",
                "--json",
                "tagName",
                "--jq",
                f'.[] | select(.tagName | startswith("{name}-v")) | .tagName',
            ]
        )
        if listing.returncode != 0:
            return
        tags = [t.strip() for t in listing.stdout.splitlines() if t.strip()]  # newest-first
        for stale in tags[self._keep :]:
            self._run(["gh", "release", "delete", stale, "--yes", "--repo", self._repo])

    def _run(self, args: Sequence[str]) -> None:
        result = self._runner.run(args)
        if result.returncode != 0:
            raise PublishError(f"{' '.join(args[:3])} failed: {result.stderr}")
