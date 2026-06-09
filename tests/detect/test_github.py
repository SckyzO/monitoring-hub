"""github-release VersionSource: argv, flag/policy filtering, errors (spec §4, §9.2)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge.detect.github import DetectError, GitHubReleaseSource
from forge.detect.registry import discover, get_source
from forge.domain.manifest import ExporterManifest, parse_manifest
from forge.packaging.runner import CommandResult


class _FakeRunner:
    """Records the last argv and replays a scripted CommandResult."""

    def __init__(self, *, stdout: str = "[]", returncode: int = 0, stderr: str = "") -> None:
        self._stdout = stdout
        self._returncode = returncode
        self._stderr = stderr
        self.calls: list[list[str]] = []

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        self.calls.append(list(args))
        return CommandResult(
            args=list(args), returncode=self._returncode, stdout=self._stdout, stderr=self._stderr
        )


def _manifest(**upstream_extra: object) -> ExporterManifest:
    manifest = parse_manifest(
        {
            "kind": "exporter",
            "name": "demo_exporter",
            "description": "demo",
            "version": "1.9.0",
            "spec": {
                "upstream": {"type": "github", "repo": "owner/demo", **upstream_extra},
                "build": {"method": "binary_repack", "binary_name": "demo_exporter"},
                "artifacts": {},
            },
        }
    )
    assert isinstance(manifest, ExporterManifest)
    return manifest


def _releases(*entries: dict[str, object]) -> str:
    return json.dumps(list(entries))


def test_source_is_registered() -> None:
    discover()
    assert get_source("github-release").type == "github-release"


def test_latest_emits_exact_argv() -> None:
    runner = _FakeRunner(
        stdout=_releases({"tagName": "v1.9.1", "isPrerelease": False, "isDraft": False})
    )
    GitHubReleaseSource().latest(_manifest(), runner=runner)
    assert runner.calls == [
        [
            "gh",
            "release",
            "list",
            "--repo",
            "owner/demo",
            "--limit",
            "30",
            "--json",
            "tagName,isPrerelease,isDraft",
        ]
    ]


def test_latest_returns_highest_stable_release() -> None:
    runner = _FakeRunner(
        stdout=_releases(
            {"tagName": "v1.9.0", "isPrerelease": False, "isDraft": False},
            {"tagName": "v1.10.0", "isPrerelease": False, "isDraft": False},
            {"tagName": "v1.9.5", "isPrerelease": False, "isDraft": False},
        )
    )
    assert GitHubReleaseSource().latest(_manifest(), runner=runner) == "v1.10.0"


def test_latest_skips_flagged_prereleases_and_drafts() -> None:
    runner = _FakeRunner(
        stdout=_releases(
            {"tagName": "v2.0.0", "isPrerelease": True, "isDraft": False},
            {"tagName": "v1.9.9", "isPrerelease": False, "isDraft": True},
            {"tagName": "v1.9.0", "isPrerelease": False, "isDraft": False},
        )
    )
    assert GitHubReleaseSource().latest(_manifest(), runner=runner) == "v1.9.0"


def test_latest_honours_major_pin() -> None:
    runner = _FakeRunner(
        stdout=_releases(
            {"tagName": "v2.0.0", "isPrerelease": False, "isDraft": False},
            {"tagName": "v1.10.0", "isPrerelease": False, "isDraft": False},
        )
    )
    assert GitHubReleaseSource().latest(_manifest(pin_major=1), runner=runner) == "v1.10.0"


def test_latest_returns_none_when_no_releases() -> None:
    runner = _FakeRunner(stdout="[]")
    assert GitHubReleaseSource().latest(_manifest(), runner=runner) is None


def test_latest_raises_on_gh_failure() -> None:
    runner = _FakeRunner(returncode=1, stderr="HTTP 404")
    with pytest.raises(DetectError, match="owner/demo"):
        GitHubReleaseSource().latest(_manifest(), runner=runner)
