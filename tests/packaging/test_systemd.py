"""Pure systemd unit rendering from the manifest Systemd block."""

from __future__ import annotations

from forge.domain.manifest import Systemd
from forge.packaging.systemd import render_systemd_unit


def test_render_unit_minimal() -> None:
    unit = render_systemd_unit(
        description="Node Exporter",
        exec_start="/usr/bin/node_exporter",
        user=None,
        systemd=Systemd(enabled=True),
    )
    assert "[Unit]" in unit
    assert "Description=Node Exporter" in unit
    assert "After=network.target" in unit
    assert "ExecStart=/usr/bin/node_exporter" in unit
    assert "Restart=on-failure" in unit
    assert "Type=simple" in unit
    assert "[Install]" in unit
    assert "WantedBy=multi-user.target" in unit
    assert "User=" not in unit


def test_render_unit_with_args_and_user() -> None:
    unit = render_systemd_unit(
        description="X",
        exec_start="/usr/bin/x",
        user="prometheus",
        systemd=Systemd(
            enabled=True,
            arguments=["--web.listen-address=:9100", "--log.level=info"],
            after=["network-online.target"],
            restart="always",
            type="notify",
        ),
    )
    assert "ExecStart=/usr/bin/x --web.listen-address=:9100 --log.level=info" in unit
    assert "After=network-online.target" in unit
    assert "Restart=always" in unit
    assert "Type=notify" in unit
    assert "User=prometheus" in unit
    assert "Group=prometheus" in unit
