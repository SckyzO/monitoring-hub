"""GitHub Releases publisher (spec §5.6): push the ./release staging tree.

Each ``<staging>/<tag>/`` subdir maps to one GitHub release whose tag is the dir
name (``rpm-el9-x86_64``, ``apt-noble``, …). For each, ensure the release exists
(``gh release view`` → ``create`` if missing) then ``gh release upload --clobber``
every asset in the dir. Idempotent: re-running clobbers assets, so per-tag URLs
are stable. Auth is ambient (``GH_TOKEN``/``GITHUB_TOKEN`` in the runner env),
never in argv. Gated by credentials in CI, like the OCI publisher.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from forge.domain.errors import PublishError
from forge.packaging.runner import CommandRunner

_NOTES = "monitoring-hub package repository"


class GitHubReleasesPublisher:
    def __init__(self, *, repo: str, runner: CommandRunner) -> None:
        self._repo = repo
        self._runner = runner

    def publish(self, staging: Path) -> None:
        for tag_dir in sorted(p for p in staging.iterdir() if p.is_dir()):
            self._publish_one(tag_dir)

    def _publish_one(self, tag_dir: Path) -> None:
        assets = sorted(p for p in tag_dir.iterdir() if p.is_file())
        if not assets:
            return
        tag = tag_dir.name
        self._ensure_release(tag)
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

    def _ensure_release(self, tag: str) -> None:
        existing = self._runner.run(["gh", "release", "view", tag, "--repo", self._repo])
        if existing.returncode == 0:
            return
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

    def prune(self, *, keep: dict[str, set[str]]) -> None:
        """Delete bucket assets not in the keep-set (mono-version, spec §4).

        ``keep`` maps a serving tag (``rpm-el9-x86_64``) to the set of current
        asset filenames to retain; every other asset in that release is deleted.
        """
        for tag, current in keep.items():
            listing = self._runner.run(
                [
                    "gh",
                    "release",
                    "view",
                    tag,
                    "--repo",
                    self._repo,
                    "--json",
                    "assets",
                    "--jq",
                    ".assets[].name",
                ]
            )
            if listing.returncode != 0:
                continue  # release absent yet -> nothing to prune
            for name in (n.strip() for n in listing.stdout.splitlines() if n.strip()):
                if name not in current:
                    self._run(
                        [
                            "gh",
                            "release",
                            "delete-asset",
                            tag,
                            name,
                            "--yes",
                            "--repo",
                            self._repo,
                        ]
                    )

    def _run(self, args: Sequence[str]) -> None:
        result = self._runner.run(args)
        if result.returncode != 0:
            raise PublishError(f"{' '.join(args[:3])} failed: {result.stderr}")
