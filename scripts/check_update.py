"""Report dev-image binary pins that are behind their latest upstream release.

``ARG <NAME>_VERSION=...`` lines in ``Dockerfile.dev`` install pinned binaries
(e.g. nfpm) via curl — something Dependabot cannot track. This script compares
each pin against the latest GitHub release of its mapped repository. Python
dependencies are covered separately by ``uv pip list --outdated`` (wired in the
``check-update`` Make target).

Exit code is non-zero when at least one pin is behind, so it can gate CI.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

# ARG <NAME>_VERSION  ->  GitHub "owner/repo" whose latest release is canonical.
TOOL_REPOS: dict[str, str] = {
    "NFPM": "goreleaser/nfpm",
}

_ARG_PIN = re.compile(r"^ARG\s+([A-Z0-9_]+?)_VERSION=(\S+)", re.MULTILINE)
_GITHUB_LATEST = "https://api.github.com/repos/{repo}/releases/latest"
_HTTP_TIMEOUT = 10
_COL = 16


def parse_dockerfile_pins(text: str) -> dict[str, str]:
    """Map ``NAME`` to its pinned version for each ``ARG NAME_VERSION=...`` line."""
    return {hit.group(1): hit.group(2) for hit in _ARG_PIN.finditer(text)}


def normalize(version: str) -> str:
    """Drop a single leading ``v`` so ``v2.46.3`` and ``2.46.3`` compare equal."""
    return version[1:] if version.startswith("v") else version


def latest_github_release(repo: str) -> str:
    """Return the latest release tag of ``owner/repo`` from the GitHub API."""
    request = urllib.request.Request(
        _GITHUB_LATEST.format(repo=repo),
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT) as response:
        payload = json.load(response)
    tag = payload.get("tag_name")
    if not isinstance(tag, str):
        raise RuntimeError(f"no string tag_name in latest release of {repo!r}")
    return tag


def main() -> int:
    dockerfile = Path(__file__).resolve().parent.parent / "Dockerfile.dev"
    pins = parse_dockerfile_pins(dockerfile.read_text(encoding="utf-8"))
    if not pins:
        print("Dev-image binary pins: none (no ARG *_VERSION in Dockerfile.dev).")
        return 0

    behind = 0
    for name, pinned in sorted(pins.items()):
        repo = TOOL_REPOS.get(name)
        if repo is None:
            print(f"  {name:<{_COL}}{pinned:<{_COL}}no upstream repo mapped (add to TOOL_REPOS)")
            continue
        latest = normalize(latest_github_release(repo))
        if normalize(pinned) == latest:
            print(f"  {name:<{_COL}}{pinned:<{_COL}}up to date")
        else:
            print(f"  {name:<{_COL}}{pinned:<{_COL}}-> {latest}  BEHIND")
            behind += 1
    return 1 if behind else 0


if __name__ == "__main__":
    sys.exit(main())
