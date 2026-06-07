"""Version-string normalization shared across packaging and fetch."""

from __future__ import annotations

import pytest

from forge.domain.version import clean_version


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("v1.9.1", "1.9.1"), ("1.9.1", "1.9.1"), ("v2", "2"), ("", ""), ("vv1", "v1")],
)
def test_clean_version_strips_single_leading_v(raw: str, expected: str) -> None:
    assert clean_version(raw) == expected
