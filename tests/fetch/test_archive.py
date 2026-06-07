"""Archive extraction + binary discovery (pure filesystem)."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from forge.domain.errors import BuildError
from forge.fetch.archive import extract_archive, find_binary


def _make_targz(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


def test_extract_targz_and_find_binary(tmp_path: Path) -> None:
    archive = tmp_path / "node_exporter-1.9.1.linux-amd64.tar.gz"
    _make_targz(
        archive,
        {"node_exporter-1.9.1.linux-amd64/node_exporter": b"ELF", "README": b"x"},
    )
    out = extract_archive(archive, tmp_path / "x")
    binary = find_binary(out, "node_exporter")
    assert binary.read_bytes() == b"ELF"
    assert binary.name == "node_exporter"


def test_extract_zip(tmp_path: Path) -> None:
    archive = tmp_path / "tool.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("dir/mybin", b"ELF")
    out = extract_archive(archive, tmp_path / "z")
    assert find_binary(out, "mybin").read_bytes() == b"ELF"


def test_extract_unsupported_format_raises(tmp_path: Path) -> None:
    archive = tmp_path / "thing.rar"
    archive.write_bytes(b"x")
    with pytest.raises(BuildError, match="unsupported archive"):
        extract_archive(archive, tmp_path / "out")


def test_find_binary_missing_raises(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "other").write_bytes(b"x")
    with pytest.raises(BuildError, match="binary 'node_exporter' not found"):
        find_binary(tmp_path, "node_exporter")
