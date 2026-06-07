"""Maintainer scriptlets for nfpm (postinstall / preremove), pure text.

systemd lifecycle and idempotent system-user creation. Kept POSIX-sh and
guarded so re-runs during upgrades do not fail. nfpm runs the same script for
both RPM and DEB; the guards make that safe.
"""

from __future__ import annotations

_HEADER = "#!/bin/sh\nset -e\n"


def render_postinstall(*, unit_name: str | None, system_user: str | None) -> str:
    blocks = [_HEADER]
    if system_user:
        # Idempotent: create the user only when getent does not already find it.
        blocks.append(
            f"getent passwd {system_user} >/dev/null 2>&1 || "
            f"useradd --system --no-create-home --shell /sbin/nologin {system_user}\n"
        )
    if unit_name:
        blocks.append(
            "systemctl daemon-reload >/dev/null 2>&1 || true\n"
            f"systemctl enable {unit_name}.service >/dev/null 2>&1 || true\n"
            f"systemctl start {unit_name}.service >/dev/null 2>&1 || true\n"
        )
    if len(blocks) == 1:
        return _HEADER.rstrip("\n")
    return "".join(blocks).rstrip("\n") + "\n"


def render_preremove(*, unit_name: str | None) -> str:
    if not unit_name:
        return _HEADER.rstrip("\n")
    return (
        _HEADER
        + f"systemctl stop {unit_name}.service >/dev/null 2>&1 || true\n"
        + f"systemctl disable {unit_name}.service >/dev/null 2>&1 || true\n"
    )
