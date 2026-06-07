"""Pure maintainer scriptlets (postinstall / preremove)."""

from __future__ import annotations

from forge.packaging.scriptlets import render_postinstall, render_preremove


def test_postinstall_systemd_and_user() -> None:
    script = render_postinstall(unit_name="node_exporter", system_user="prometheus")
    assert script.startswith("#!/bin/sh\nset -e\n")
    assert "getent passwd prometheus" in script
    assert "useradd --system" in script
    assert "systemctl daemon-reload" in script
    assert "systemctl enable node_exporter.service" in script
    assert "systemctl start node_exporter.service" in script


def test_postinstall_no_systemd_no_user_is_noop() -> None:
    script = render_postinstall(unit_name=None, system_user=None)
    assert script.strip() == "#!/bin/sh\nset -e"
    assert "systemctl" not in script
    assert "useradd" not in script


def test_postinstall_user_creation_is_idempotent() -> None:
    # user block must be guarded so re-runs / upgrades do not fail
    script = render_postinstall(unit_name=None, system_user="prometheus")
    assert "getent passwd prometheus >/dev/null" in script
    assert "||" in script  # create only when getent fails


def test_preremove_disables_unit() -> None:
    script = render_preremove(unit_name="node_exporter")
    assert "systemctl stop node_exporter.service" in script
    assert "systemctl disable node_exporter.service" in script


def test_preremove_noop_without_unit() -> None:
    assert render_preremove(unit_name=None).strip() == "#!/bin/sh\nset -e"
