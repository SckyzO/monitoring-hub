"""HttpxDownloader.exists: HEAD probe returning True only on 2xx."""

from __future__ import annotations

import httpx
import pytest

from forge.fetch.http import HttpxDownloader

_RealClient = httpx.Client


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return _RealClient(transport=handler)


def test_exists_true_on_200(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(200))
    monkeypatch.setattr(httpx, "Client", lambda **kw: _client(transport))
    assert HttpxDownloader().exists("https://x/repomd.xml") is True


def test_exists_false_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(404))
    monkeypatch.setattr(httpx, "Client", lambda **kw: _client(transport))
    assert HttpxDownloader().exists("https://x/repomd.xml") is False
