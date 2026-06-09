"""Watch orchestration: source-type mapping + DetectedVersion build (spec §4, §8)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

import forge.detect.watch as watch_mod
from forge.detect.base import DetectedVersion
from forge.detect.watch import detect_all, resolve_source_type
from forge.domain.manifest import Manifest, parse_manifest
from forge.packaging.runner import CommandResult


class _StubRunner:
    """A runner whose output is irrelevant — the source is patched in these tests."""

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        return CommandResult(args=list(args), returncode=0, stdout="[]", stderr="")


def _exporter(version: str = "1.9.0", **upstream_extra: object) -> Manifest:
    return parse_manifest(
        {
            "kind": "exporter",
            "name": "demo_exporter",
            "description": "demo",
            "version": version,
            "spec": {
                "upstream": {"type": "github", "repo": "owner/demo", **upstream_extra},
                "build": {"method": "binary_repack", "binary_name": "demo_exporter"},
                "artifacts": {},
            },
        }
    )


def _local_exporter() -> Manifest:
    return parse_manifest(
        {
            "kind": "exporter",
            "name": "local_exporter",
            "description": "demo",
            "version": "1.0.0",
            "spec": {
                "upstream": {"type": "local", "local_binary": "demo"},
                "build": {"method": "binary_repack", "binary_name": "demo"},
                "artifacts": {},
            },
        }
    )


def _dashboard() -> Manifest:
    return parse_manifest(
        {
            "kind": "dashboard",
            "name": "demo_dash",
            "description": "demo",
            "version": "1",
            "spec": {"source": {"type": "grafana", "id": 1, "revision": 1}},
        }
    )


def test_resolve_source_type_github_exporter() -> None:
    assert resolve_source_type(_exporter()) == "github-release"


def test_resolve_source_type_local_is_none() -> None:
    assert resolve_source_type(_local_exporter()) is None


def test_resolve_source_type_dashboard_is_none() -> None:
    assert resolve_source_type(_dashboard()) is None


class _FakeSource:
    type = "github-release"

    def __init__(self, latest: str | None) -> None:
        self._latest = latest

    def latest(self, manifest: object, *, runner: object) -> str | None:
        return self._latest


def test_detect_all_builds_detected_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("forge.detect.watch.get_source", lambda _t: _FakeSource("v1.10.0"))
    result = detect_all([_exporter(version="1.9.0")], runner=_StubRunner())
    assert result == [
        DetectedVersion(
            item="demo_exporter",
            kind="exporter",
            current="1.9.0",
            latest="1.10.0",
            latest_raw="v1.10.0",
            source_type="github-release",
            outdated=True,
        )
    ]


def test_detect_all_marks_up_to_date_not_outdated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("forge.detect.watch.get_source", lambda _t: _FakeSource("v1.9.0"))
    [detected] = detect_all([_exporter(version="1.9.0")], runner=_StubRunner())
    assert detected.outdated is False
    assert detected.latest == "1.9.0"


def test_detect_all_skips_unwatchable_and_undetectable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("forge.detect.watch.get_source", lambda _t: _FakeSource(None))
    manifests = [_local_exporter(), _exporter()]
    assert detect_all(manifests, runner=_StubRunner()) == []


def test_detect_one_keeps_raw_and_clean_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _exporter(version="v1.9.0")
    monkeypatch.setattr(
        watch_mod,
        "get_source",
        lambda _type: type("S", (), {"latest": lambda self, m, *, runner: "v1.10.0"})(),
    )
    detected = watch_mod.detect_one(manifest, runner=_StubRunner())
    assert detected is not None
    assert detected.latest_raw == "v1.10.0"
    assert detected.latest == "1.10.0"
    assert detected.current == "1.9.0"
    assert detected.outdated is True
