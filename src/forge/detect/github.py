"""``github-release`` version source (spec §4).

Lists a repository's releases via the ``gh`` CLI (ambient ``GH_TOKEN`` auth,
never in argv) and returns the latest acceptable tag. Draft and GitHub-flagged
pre-releases are dropped here; the source-agnostic ``policy`` applies the
remaining rules (regex pre-release guard, optional major pin, numeric ordering).
"""

from __future__ import annotations

import json

from forge.detect import policy
from forge.detect.registry import register
from forge.domain.errors import ForgeError
from forge.domain.manifest import ExporterManifest, Manifest
from forge.packaging.runner import CommandRunner

_LIMIT = "30"
_JSON_FIELDS = "tagName,isPrerelease,isDraft"


class DetectError(ForgeError):
    """An upstream version could not be detected (e.g. the ``gh`` call failed)."""


@register("github-release")
class GitHubReleaseSource:
    type = "github-release"

    def latest(self, manifest: Manifest, *, runner: CommandRunner) -> str | None:
        if not isinstance(manifest, ExporterManifest):
            return None
        repo = manifest.spec.upstream.repo
        if repo is None:
            return None
        result = runner.run(
            ["gh", "release", "list", "--repo", repo, "--limit", _LIMIT, "--json", _JSON_FIELDS]
        )
        if result.returncode != 0:
            raise DetectError(f"gh release list failed for {repo}: {result.stderr.strip()}")
        releases = json.loads(result.stdout or "[]")
        candidates = [
            str(entry["tagName"])
            for entry in releases
            if not entry.get("isDraft", False) and not entry.get("isPrerelease", False)
        ]
        return policy.select_latest(candidates, pin_major=manifest.spec.upstream.pin_major)
