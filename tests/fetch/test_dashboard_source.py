"""Dashboard source URL resolution (pure)."""

from __future__ import annotations

from forge.domain.manifest import GitSource, GrafanaSource, LocalSource, UrlSource
from forge.fetch.dashboard_source import resolve_dashboard_url


def test_grafana_source_url() -> None:
    url = resolve_dashboard_url(GrafanaSource(type="grafana", id=1860, revision=39))
    assert url == "https://grafana.com/api/dashboards/1860/revisions/39/download"


def test_url_source_passthrough() -> None:
    url = resolve_dashboard_url(UrlSource(type="url", url="https://example.test/d.json"))
    assert url == "https://example.test/d.json"


def test_git_source_raw_github() -> None:
    url = resolve_dashboard_url(
        GitSource(type="git", repo="o/r", ref="v1.0.0", path="dash/node.json")
    )
    assert url == "https://raw.githubusercontent.com/o/r/v1.0.0/dash/node.json"


def test_local_source_returns_none() -> None:
    assert resolve_dashboard_url(LocalSource(type="local", path="dash.json")) is None
