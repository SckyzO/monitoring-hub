"""CatalogEntry: one item in catalog.json (spec §6.2, §10).

new/updated are catalog-build state, NOT manifest fields — they live here.
"""

from __future__ import annotations

from forge.domain.artifact import Artifact
from forge.domain.catalog import CatalogEntry


def test_state_flags_default_false_and_artifacts_empty() -> None:
    entry = CatalogEntry(
        kind="dashboard",
        name="node-overview",
        version="39",
        category="System",
        description="Node Exporter Full",
    )
    assert entry.new is False
    assert entry.updated is False
    assert entry.artifacts == []


def test_entry_carries_artifacts() -> None:
    entry = CatalogEntry(
        kind="exporter",
        name="node_exporter",
        version="1.11.1",
        category="System",
        description="Hardware and OS metrics",
        artifacts=[Artifact(type="rpm", target="el9", arch="x86_64", sha256="x", signed=True)],
        new=True,
    )
    assert entry.new is True
    assert entry.artifacts[0].type == "rpm"
