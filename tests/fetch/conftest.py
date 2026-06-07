"""Fetch-layer test doubles: an in-memory Downloader that writes canned bytes."""

from __future__ import annotations

from pathlib import Path


class FakeDownloader:
    """Records requested URLs; writes ``payload`` to every requested dest."""

    def __init__(self, payload: bytes = b"") -> None:
        self.payload = payload
        self.urls: list[str] = []

    def download(self, url: str, dest: Path) -> Path:
        self.urls.append(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.payload)
        return dest
