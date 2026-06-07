"""HTTP download seam (spec §7.1, §16).

``Downloader`` is the single network boundary for producers; tests inject a
fake so the unit suite never touches the network. ``HttpxDownloader`` streams
to disk and retries transient failures via ``tenacity``. Any failure to fetch
is wrapped as ``SourceResolutionError`` (spec §14: wrap the op that can fail).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from forge.domain.errors import SourceResolutionError

_CHUNK = 1024 * 1024


@runtime_checkable
class Downloader(Protocol):
    def download(self, url: str, dest: Path) -> Path: ...


class HttpxDownloader:
    """Real downloader: streams ``url`` to ``dest`` with bounded retries."""

    def __init__(self, *, timeout: float = 30.0, retries: int = 3) -> None:
        self._timeout = timeout
        self._retries = retries

    def download(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)

        @retry(
            retry=retry_if_exception_type(httpx.TransportError),
            stop=stop_after_attempt(self._retries),
            wait=wait_exponential(multiplier=0.5, max=8),
            reraise=True,
        )
        def _fetch() -> None:
            with (
                httpx.Client(timeout=self._timeout, follow_redirects=True) as client,
                client.stream("GET", url) as response,
            ):
                response.raise_for_status()
                with dest.open("wb") as handle:
                    for chunk in response.iter_bytes(_CHUNK):
                        handle.write(chunk)

        try:
            _fetch()
        except (httpx.HTTPError, OSError) as exc:
            raise SourceResolutionError(f"download failed for {url}: {exc}") from exc
        return dest
