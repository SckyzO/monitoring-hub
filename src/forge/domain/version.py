"""Manifest version-string helpers (pure, dependency-free)."""

from __future__ import annotations


def clean_version(version: str) -> str:
    """Strip a single leading ``v`` so ``v1.9.1`` and ``1.9.1`` are equal."""
    return version[1:] if version.startswith("v") else version
