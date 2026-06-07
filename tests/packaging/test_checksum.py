"""Streamed SHA-256 of artifact files."""

from __future__ import annotations

import hashlib
from pathlib import Path

from forge.packaging.checksum import file_sha256


def test_file_sha256_matches_known_digest(tmp_path: Path) -> None:
    f = tmp_path / "blob"
    f.write_bytes(b"forge")
    # echo -n forge | sha256sum
    assert file_sha256(f) == "71b41d6dd48dc58eba8f5cf9edf30fef6597fdf285a521bb8fcbad4b3d50887d"


def test_file_sha256_streams_large_file(tmp_path: Path) -> None:
    f = tmp_path / "big"
    payload = b"x" * (1024 * 1024 + 7)
    f.write_bytes(payload)
    assert file_sha256(f) == hashlib.sha256(payload).hexdigest()
