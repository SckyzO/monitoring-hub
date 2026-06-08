"""Typed error hierarchy for the forge engine (spec §14).

Every failure surfaces the real cause. The CLI catches ``ForgeError`` at the
top level, prints the cause, and exits non-zero. No layer swallows errors and
returns a default.
"""

from __future__ import annotations


class ForgeError(Exception):
    """Base class for every error raised by the forge engine."""


class ManifestError(ForgeError):
    """A manifest is missing, malformed, or fails schema/semantic validation."""


class SourceResolutionError(ForgeError):
    """A manifest source (catalogue / file / dir / upstream) cannot be resolved."""


class BuildError(ForgeError):
    """An artifact build step failed."""


class SigningError(ForgeError):
    """Signing an artifact failed."""


class CommandError(ForgeError):
    """A subprocess could not be launched (missing binary, OS-level error)."""


class DistributionError(ForgeError):
    """Generating a repository tree (rpm/apt metadata, signing) failed."""


class PublishError(ForgeError):
    """Publishing artifacts to a remote (GitHub Releases, OCI registry) failed."""


class BundleError(ForgeError):
    """Building an offline bundle failed (recipe load, item resolution, fetch)."""
