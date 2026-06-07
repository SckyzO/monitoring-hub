"""Resolve a dashboard ``spec.source`` to a download URL (spec §7.2).

Pure: maps each discriminated source shape to a URL. ``local`` returns ``None``
(the producer reads it from the manifest dir instead of downloading).
"""

from __future__ import annotations

from forge.domain.errors import SourceResolutionError
from forge.domain.manifest import (
    DashboardSource,
    GitSource,
    GrafanaSource,
    LocalSource,
    UrlSource,
)

_GRAFANA_API = "https://grafana.com/api/dashboards/{id}/revisions/{revision}/download"
_GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def resolve_dashboard_url(source: DashboardSource) -> str | None:
    """Return the download URL for ``source``; ``None`` for a local source."""
    match source:
        case GrafanaSource():
            return _GRAFANA_API.format(id=source.id, revision=source.revision)
        case UrlSource():
            return source.url
        case GitSource():
            return _GITHUB_RAW.format(repo=source.repo, ref=source.ref, path=source.path)
        case LocalSource():
            return None
        case _:  # pragma: no cover - exhaustive over the discriminated union
            raise SourceResolutionError(f"unsupported dashboard source: {source!r}")
