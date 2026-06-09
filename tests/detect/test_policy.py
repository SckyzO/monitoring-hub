"""Version policy: pre-release filter, numeric compare, major pin (spec §4)."""

from __future__ import annotations

import pytest

from forge.detect.policy import (
    is_newer,
    is_prerelease,
    major_of,
    passes_major_pin,
    select_latest,
    version_key,
)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.2.3", False),
        ("v1.2.3", False),
        ("2.0.0-rc1", True),
        ("1.0.0-beta.2", True),
        ("1.0.0-alpha", True),
        ("1.5.0-pre", True),
        ("0.9.0-dev", True),
        ("1.2.3-RC2", True),
        ("1.10.0", False),
    ],
)
def test_is_prerelease(version: str, expected: bool) -> None:
    assert is_prerelease(version) is expected


def test_version_key_strips_leading_v_and_splits() -> None:
    assert version_key("v1.9.1") == (1, 9, 1)
    assert version_key("1.9") == (1, 9)


def test_version_key_numeric_ordering_beats_string() -> None:
    assert version_key("1.10.0") > version_key("1.9.0")


def test_version_key_stops_at_first_non_numeric_chunk() -> None:
    assert version_key("1.2.3+build7") == (1, 2)
    assert version_key("1.2.foo") == (1, 2)


@pytest.mark.parametrize(
    ("candidate", "current", "expected"),
    [
        ("1.9.2", "1.9.1", True),
        ("v1.9.2", "1.9.1", True),
        ("1.9.1", "1.9.1", False),
        ("1.9.0", "1.9.1", False),
        ("1.10.0", "1.9.9", True),
        ("2.0.0", "1.99.0", True),
    ],
)
def test_is_newer(candidate: str, current: str, expected: bool) -> None:
    assert is_newer(candidate, current) is expected


def test_major_of() -> None:
    assert major_of("v2.3.4") == 2
    assert major_of("") is None


@pytest.mark.parametrize(
    ("version", "pin", "expected"),
    [
        ("1.9.0", None, True),
        ("1.9.0", 1, True),
        ("2.0.0", 1, False),
        ("2.0.0", 2, True),
    ],
)
def test_passes_major_pin(version: str, pin: int | None, expected: bool) -> None:
    assert passes_major_pin(version, pin) is expected


def test_select_latest_picks_highest_stable() -> None:
    tags = ["v1.9.0", "v1.10.0", "v1.9.5"]
    assert select_latest(tags) == "v1.10.0"


def test_select_latest_skips_prereleases() -> None:
    tags = ["v2.0.0-rc1", "v1.9.0"]
    assert select_latest(tags) == "v1.9.0"


def test_select_latest_honours_major_pin() -> None:
    tags = ["v2.0.0", "v1.9.0", "v1.10.0"]
    assert select_latest(tags, pin_major=1) == "v1.10.0"


def test_select_latest_returns_none_when_nothing_acceptable() -> None:
    assert select_latest(["v2.0.0-rc1"]) is None
    assert select_latest([]) is None
    assert select_latest(["v3.0.0"], pin_major=1) is None
