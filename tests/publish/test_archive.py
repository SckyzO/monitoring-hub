"""ArchiveReleasesPublisher: per-version release + keep-newest-N retention."""

from __future__ import annotations

from pathlib import Path

from forge.packaging.runner import CommandResult
from forge.publish.archive import ArchiveReleasesPublisher


class ArchiveRunner:
    def __init__(self, existing: list[str]) -> None:
        self.calls: list[list[str]] = []
        self._existing = existing  # newest-first {name}-v* tags

    def run(self, args, *, cwd=None, env=None, stdin=None):  # type: ignore[no-untyped-def]
        argv = list(args)
        self.calls.append(argv)
        if argv[:3] == ["gh", "release", "list"]:
            return CommandResult(
                args=argv, returncode=0, stdout="\n".join(self._existing), stderr=""
            )
        if argv[:3] == ["gh", "release", "view"]:
            return CommandResult(args=argv, returncode=1, stdout="", stderr="")  # force create
        return CommandResult(args=argv, returncode=0, stdout="", stderr="")


def _asset(d: Path, name: str) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_bytes(b"x")
    return p


def test_archive_creates_versioned_release_and_uploads(tmp_path: Path) -> None:
    assets = [
        _asset(tmp_path, "node_exporter-1.12.0-1.el9.x86_64.rpm"),
        _asset(tmp_path, "node-exporter_1.12.0-1_amd64.deb"),
    ]
    runner = ArchiveRunner(existing=[])
    ArchiveReleasesPublisher(repo="o/r", runner=runner, keep=10).publish_item(
        name="node_exporter", version="1.12.0", assets=assets
    )
    flat = [" ".join(c) for c in runner.calls]
    assert any("gh release create node_exporter-v1.12.0 --repo o/r" in c for c in flat)
    assert any("gh release upload node_exporter-v1.12.0" in c and ".rpm" in c for c in flat)


def test_archive_retention_deletes_beyond_keep(tmp_path: Path) -> None:
    existing = [f"node_exporter-v1.{n}.0" for n in range(12, 0, -1)]  # 12 newest-first
    runner = ArchiveRunner(existing=existing)
    ArchiveReleasesPublisher(repo="o/r", runner=runner, keep=10).enforce_retention("node_exporter")
    deleted = [c for c in runner.calls if c[:3] == ["gh", "release", "delete"]]
    assert len(deleted) == 2  # 12 - 10
    assert ["gh", "release", "delete", "node_exporter-v1.2.0", "--yes", "--repo", "o/r"] in deleted
    assert ["gh", "release", "delete", "node_exporter-v1.1.0", "--yes", "--repo", "o/r"] in deleted
