"""GitHubReleasesPublisher: emits gh release view/create/upload --clobber."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge.domain.errors import PublishError
from forge.packaging.runner import CommandResult
from forge.publish.releases import GitHubReleasesPublisher


class RecordingRunner:
    """Records argv; `view` returns `view_rc`, optionally fails one verb."""

    def __init__(self, *, view_rc: int = 1, fail_verb: str | None = None) -> None:
        self.calls: list[list[str]] = []
        self._view_rc = view_rc
        self._fail_verb = fail_verb

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        argv = list(args)
        self.calls.append(argv)
        rc = 0
        if argv[:3] == ["gh", "release", "view"]:
            rc = self._view_rc
        if self._fail_verb is not None and len(argv) > 2 and argv[2] == self._fail_verb:
            rc = 1
        return CommandResult(args=argv, returncode=rc, stdout="", stderr="boom")


def _tag_dir(staging: Path, tag: str, *files: str) -> None:
    d = staging / tag
    d.mkdir(parents=True)
    for f in files:
        (d / f).write_bytes(b"x")


def test_creates_release_when_missing_then_uploads(tmp_path: Path) -> None:
    staging = tmp_path / "release"
    _tag_dir(staging, "rpm-el9-x86_64", "node_exporter-1.9.1-1.el9.x86_64.rpm")
    runner = RecordingRunner(view_rc=1)

    GitHubReleasesPublisher(repo="o/r", runner=runner).publish(staging)

    flat = [" ".join(c) for c in runner.calls]
    assert any("gh release view rpm-el9-x86_64 --repo o/r" in c for c in flat)
    assert any(
        c.startswith("gh release create rpm-el9-x86_64 --repo o/r")
        and "--title rpm-el9-x86_64" in c
        and "--notes" in c
        for c in flat
    )
    assert any(
        "gh release upload rpm-el9-x86_64" in c
        and "node_exporter-1.9.1-1.el9.x86_64.rpm" in c
        and "--clobber" in c
        and "--repo o/r" in c
        for c in flat
    )


def test_skips_create_when_release_exists(tmp_path: Path) -> None:
    staging = tmp_path / "release"
    _tag_dir(staging, "apt-noble", "Packages", "node-exporter_1.9.1-1_amd64.deb")
    runner = RecordingRunner(view_rc=0)

    GitHubReleasesPublisher(repo="o/r", runner=runner).publish(staging)

    flat = [" ".join(c) for c in runner.calls]
    assert not any("gh release create" in c for c in flat)
    assert any("gh release upload apt-noble" in c for c in flat)


def test_uploads_all_assets_in_one_call(tmp_path: Path) -> None:
    staging = tmp_path / "release"
    _tag_dir(staging, "apt-noble", "InRelease", "Release", "Packages", "x_1-1_amd64.deb")
    runner = RecordingRunner(view_rc=0)

    GitHubReleasesPublisher(repo="o/r", runner=runner).publish(staging)

    upload = next(c for c in runner.calls if c[:3] == ["gh", "release", "upload"])
    for asset in ("InRelease", "Release", "Packages", "x_1-1_amd64.deb"):
        assert any(asset in part for part in upload)


def test_skips_empty_tag_dir(tmp_path: Path) -> None:
    staging = tmp_path / "release"
    (staging / "empty").mkdir(parents=True)
    runner = RecordingRunner(view_rc=1)

    GitHubReleasesPublisher(repo="o/r", runner=runner).publish(staging)

    assert runner.calls == []


def test_raises_on_upload_failure(tmp_path: Path) -> None:
    staging = tmp_path / "release"
    _tag_dir(staging, "rpm-el9-x86_64", "p.rpm")
    runner = RecordingRunner(view_rc=0, fail_verb="upload")

    with pytest.raises(PublishError, match="gh release upload failed: boom"):
        GitHubReleasesPublisher(repo="o/r", runner=runner).publish(staging)


def test_prune_deletes_superseded_assets_per_coordinate(tmp_path: Path) -> None:
    """Given the current versions, delete every other version of the same package
    in each serving bucket; keep the current ones."""

    class ListingRunner(RecordingRunner):
        def run(self, args, *, cwd=None, env=None, stdin=None):  # type: ignore[no-untyped-def]
            argv = list(args)
            self.calls.append(argv)
            if argv[:3] == ["gh", "release", "view"] and "rpm-el9-x86_64" in argv:
                return CommandResult(
                    args=argv,
                    returncode=0,
                    stdout=(
                        "node_exporter-1.11.1-1.el9.x86_64.rpm\n"
                        "node_exporter-1.12.0-1.el9.x86_64.rpm\n"
                    ),
                    stderr="",
                )
            return CommandResult(args=argv, returncode=0, stdout="", stderr="")

    runner = ListingRunner(view_rc=0)
    GitHubReleasesPublisher(repo="o/r", runner=runner).prune(
        keep={"rpm-el9-x86_64": {"node_exporter-1.12.0-1.el9.x86_64.rpm"}}
    )
    flat = [" ".join(c) for c in runner.calls]
    assert any(
        "release delete-asset rpm-el9-x86_64 node_exporter-1.11.1-1.el9.x86_64.rpm" in c
        for c in flat
    )
    assert not any("delete-asset rpm-el9-x86_64 node_exporter-1.12.0-1" in c for c in flat)
