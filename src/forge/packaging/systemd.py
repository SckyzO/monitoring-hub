"""Render a systemd service unit from the manifest ``Systemd`` block (pure).

Faithful port of the legacy ``default.spec.j2`` systemd section: ``ExecStart``
is the binary plus its arguments; ``After``/``Restart``/``Type`` come from the
model; a ``user`` adds matching ``User=``/``Group=`` lines.
"""

from __future__ import annotations

from forge.domain.manifest import Systemd


def render_systemd_unit(
    *, description: str, exec_start: str, user: str | None, systemd: Systemd
) -> str:
    after = " ".join(systemd.after)
    exec_line = exec_start
    if systemd.arguments:
        exec_line = f"{exec_start} {' '.join(systemd.arguments)}"

    lines = [
        "[Unit]",
        f"Description={description}",
        f"After={after}",
        "",
        "[Service]",
        f"Type={systemd.type}",
    ]
    if user:
        lines += [f"User={user}", f"Group={user}"]
    lines += [
        f"ExecStart={exec_line}",
        f"Restart={systemd.restart}",
        "",
        "[Install]",
        "WantedBy=multi-user.target",
        "",
    ]
    return "\n".join(lines)
