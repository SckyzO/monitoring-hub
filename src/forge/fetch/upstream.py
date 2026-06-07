"""Resolve a GitHub release download URL from the manifest upstream (pure).

The download tag is the manifest version as-is (preserves the upstream ``v``
prefix); the archive filename is a template with ``{name} {version}
{clean_version} {arch}`` placeholders, or a per-arch mapping. An unsupported
upstream, a missing per-arch entry, or an unknown placeholder is a
``SourceResolutionError`` (no silent default).
"""

from __future__ import annotations

from forge.domain.errors import SourceResolutionError
from forge.domain.manifest import Upstream
from forge.domain.version import clean_version

_DEFAULT_ARCHIVE = "{name}-{clean_version}.linux-{arch}.tar.gz"


def resolve_download_url(upstream: Upstream, *, name: str, version: str, arch: str) -> str:
    if upstream.type != "github" or not upstream.repo:
        raise SourceResolutionError(
            f"download URL needs a github upstream with a repo, got {upstream.type!r}"
        )

    template = upstream.archive_name
    if isinstance(template, dict):
        chosen = template.get(arch)
        if chosen is None:
            raise SourceResolutionError(f"no archive_name for arch {arch!r}")
        tmpl = chosen
    else:
        tmpl = template or _DEFAULT_ARCHIVE

    try:
        filename = tmpl.format(
            name=name, version=version, clean_version=clean_version(version), arch=arch
        )
    except KeyError as exc:
        raise SourceResolutionError(
            f"unknown placeholder {exc} in archive_name template {tmpl!r}"
        ) from exc

    return f"https://github.com/{upstream.repo}/releases/download/{version}/{filename}"
