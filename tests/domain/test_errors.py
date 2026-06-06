"""The typed error hierarchy all layers raise (spec §14)."""

from __future__ import annotations

import pytest

from forge.domain.errors import (
    BuildError,
    CommandError,
    ForgeError,
    ManifestError,
    SigningError,
    SourceResolutionError,
)


@pytest.mark.parametrize(
    "subclass",
    [ManifestError, SourceResolutionError, BuildError, SigningError, CommandError],
)
def test_all_errors_subclass_forge_error(subclass: type[ForgeError]) -> None:
    assert issubclass(subclass, ForgeError)


def test_forge_error_is_an_exception() -> None:
    assert issubclass(ForgeError, Exception)
    with pytest.raises(ForgeError):
        raise ManifestError("boom")


def test_command_error_is_forge_error() -> None:
    err = CommandError("nfpm not found")
    assert isinstance(err, ForgeError)
    assert str(err) == "nfpm not found"
