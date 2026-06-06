"""Tooling adapters: nfpm (RPM/DEB), Docker build, GPG sign (spec §4, §7.1).

Pure render/config functions carry the packaging contract (golden-tested);
thin adapter classes orchestrate them behind an injected ``CommandRunner`` so
the unit suite runs with no external tools (spec §15).
"""
