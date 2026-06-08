"""Pure rpm/deb naming convention (single source of truth, spec §2.1)."""

from __future__ import annotations

import pytest

from forge.domain.errors import DistributionError
from forge.repo.naming import codename_for, deb_filename, rpm_arch, rpm_filename


def test_rpm_arch_known() -> None:
    assert rpm_arch("amd64") == "x86_64"
    assert rpm_arch("arm64") == "aarch64"


def test_rpm_arch_unknown_raises() -> None:
    with pytest.raises(DistributionError, match="no rpm arch mapping"):
        rpm_arch("riscv64")


def test_codename_for_known() -> None:
    assert codename_for("ubuntu-24.04") == "noble"
    assert codename_for("debian-13") == "trixie"
    assert codename_for("ubuntu-26.04") == "resolute"


def test_codename_for_unknown_raises() -> None:
    with pytest.raises(DistributionError, match="no apt codename"):
        codename_for("fedora-40")


def test_rpm_filename() -> None:
    assert rpm_filename("node_exporter", "1.9.1", "el9", "x86_64") == (
        "node_exporter-1.9.1-1.el9.x86_64.rpm"
    )


def test_deb_filename_hyphenates_name() -> None:
    assert deb_filename("node_exporter", "1.9.1", "amd64") == "node-exporter_1.9.1-1_amd64.deb"
