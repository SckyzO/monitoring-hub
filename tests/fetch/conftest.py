"""Fetch-layer test doubles: an in-memory Downloader that writes canned bytes."""

from __future__ import annotations

from pathlib import Path


class FakeDownloader:
    """Records requested URLs; writes ``payload`` to every requested dest."""

    def __init__(self, payload: bytes = b"", *, present: bool = True) -> None:
        self.payload = payload
        self.urls: list[str] = []
        self.present = present

    def download(self, url: str, dest: Path) -> Path:
        self.urls.append(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.payload)
        return dest

    def exists(self, url: str) -> bool:
        self.urls.append(url)
        return self.present
