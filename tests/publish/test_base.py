"""The Publisher protocol is the host-agnostic publish contract."""

from __future__ import annotations

from pathlib import Path

from forge.publish.base import Publisher


class _FakePublisher:
    def __init__(self) -> None:
        self.published: list[Path] = []

    def publish(self, staging: Path) -> None:
        self.published.append(staging)


def test_conforming_object_is_a_publisher() -> None:
    assert isinstance(_FakePublisher(), Publisher)


def test_non_conforming_object_is_not_a_publisher() -> None:
    assert not isinstance(object(), Publisher)


def test_publish_receives_the_staging_path() -> None:
    pub = _FakePublisher()
    pub.publish(Path("/tmp/release"))
    assert pub.published == [Path("/tmp/release")]
