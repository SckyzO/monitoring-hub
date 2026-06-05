"""Artifact: one build output (spec §6.3). 1 kind → N artifacts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from forge.domain.artifact import Artifact


def test_minimal_artifact_defaults() -> None:
    art = Artifact(type="grafana-dashboard", sha256="abc123")
    assert art.target is None
    assert art.arch is None
    assert art.url is None
    assert art.signed is False


def test_full_artifact_roundtrip() -> None:
    art = Artifact(
        type="rpm",
        target="el9",
        arch="x86_64",
        url=None,
        sha256="deadbeef",
        signed=True,
    )
    assert art.model_dump() == {
        "type": "rpm",
        "target": "el9",
        "arch": "x86_64",
        "url": None,
        "sha256": "deadbeef",
        "signed": True,
    }


def test_sha256_is_required() -> None:
    with pytest.raises(ValidationError):
        Artifact(type="rpm")  # type: ignore[call-arg]


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Artifact(type="rpm", sha256="x", bogus=1)  # type: ignore[call-arg]
