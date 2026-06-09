"""L3 reconcile self-healing smoke (spec §7): build a real exporter, assemble
a catalogue, drop one leg, prove reconcile detects it, rebuild, re-assemble,
prove the catalogue is complete (missing == []).

Gated by FORGE_DOCKER_TESTS=1; needs nfpm + network to download the upstream
binary and produce a real RPM. Runs OUTSIDE ``make ci`` (forge-smoke.yml),
like the other L3 smokes.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from forge.catalog.builder import load_catalog, write_catalog
from forge.cli.main import cli
from forge.domain.manifest import (
    Build,
    DebTarget,
    DockerTarget,
    ExporterArtifacts,
    ExporterManifest,
    ExporterSpec,
    RpmTarget,
    Systemd,
    Upstream,
)
from forge.fetch.http import HttpxDownloader
from forge.kinds.base import BuildContext
from forge.kinds.exporter import ExporterProducer
from forge.packaging.runner import SubprocessRunner

pytestmark = pytest.mark.skipif(
    os.environ.get("FORGE_DOCKER_TESTS") != "1" or any(shutil.which(t) is None for t in ("nfpm",)),
    reason="set FORGE_DOCKER_TESTS=1 with nfpm available",
)

_VERSION = "v1.9.1"
_NAME = "node_exporter"
_TARGET = "el9"
_ARCH = "amd64"


def _manifest() -> ExporterManifest:
    """Minimal RPM-only manifest: one arch × one target to keep runtime bounded."""
    return ExporterManifest(
        kind="exporter",
        name=_NAME,
        description="Prometheus exporter for hardware and OS metrics",
        category="System",
        version=_VERSION,
        license="Apache-2.0",
        spec=ExporterSpec(
            upstream=Upstream(type="github", repo="prometheus/node_exporter"),
            build=Build(method="binary_repack", binary_name=_NAME, archs=[_ARCH]),
            artifacts=ExporterArtifacts(
                rpm=RpmTarget(
                    enabled=True,
                    targets=[_TARGET],
                    summary="Node exporter",
                    systemd=Systemd(enabled=True),
                    system_user="prometheus",
                ),
                deb=DebTarget(enabled=False),
                docker=DockerTarget(enabled=False),
            ),
        ),
    )


def _catalog_root(tmp_path: Path) -> Path:
    """Write a minimal catalog root with the manifest so reconcile can compute
    the expected leg matrix.  Only rpm/el9/amd64 is declared — matches _manifest().
    """
    root = tmp_path / "catalog-root"
    item_dir = root / "exporters" / _NAME
    item_dir.mkdir(parents=True)
    (item_dir / "manifest.yaml").write_text(
        "\n".join(
            [
                "kind: exporter",
                f"name: {_NAME}",
                f"version: {_VERSION}",
                f"description: {_NAME}",
                "category: System",
                "spec:",
                "  upstream:",
                "    type: github",
                "    repo: prometheus/node_exporter",
                "  build:",
                "    method: binary_repack",
                f"    binary_name: {_NAME}",
                f"    archs: [{_ARCH}]",
                "  artifacts:",
                "    rpm:",
                "      enabled: true",
                f"      targets: [{_TARGET}]",
                "    deb:",
                "      enabled: false",
                "    docker:",
                "      enabled: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def _build_exporter(work_dir: Path, entry_out: Path) -> None:
    """Run a real ExporterProducer build and write entry.json to *entry_out*."""
    from forge.catalog.entries import write_entry  # noqa: PLC0415

    ctx = BuildContext(
        work_dir=work_dir,
        downloader=HttpxDownloader(),
        runner=SubprocessRunner(),
    )
    result = ExporterProducer().build(_manifest(), ctx)
    write_entry(result.entry, entry_out)


def _reconcile_json(
    catalog_root: Path,
    catalog_path: Path,
) -> dict[str, object]:
    """Invoke ``mh catalog reconcile --json`` in-process via CliRunner."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "catalog",
            "reconcile",
            "--catalog-root",
            str(catalog_root),
            "--catalog",
            str(catalog_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload: dict[str, object] = json.loads(result.output)
    return payload


def _assemble(
    entries_dir: Path,
    output: Path,
    *,
    previous: Path | None = None,
) -> None:
    """Invoke ``mh catalog assemble`` in-process via CliRunner."""
    args = ["catalog", "assemble", "--entries", str(entries_dir), "--output", str(output)]
    if previous is not None:
        args += ["--previous", str(previous)]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output


def test_reconcile_self_healing_loop(tmp_path: Path) -> None:
    """Self-healing loop: build → assemble → drop leg → detect → re-assemble → healed."""
    catalog_root = _catalog_root(tmp_path)
    work_dir = tmp_path / "build"
    entry_out = tmp_path / "entries"
    catalog_path = tmp_path / "catalog.json"

    # Step 1 — build a real exporter and write its entry.json.
    _build_exporter(work_dir, entry_out)

    # Step 2 — assemble a catalogue from the entry.
    _assemble(entry_out, catalog_path)

    # Step 3 — sanity: catalogue is complete right after the build.
    payload = _reconcile_json(catalog_root, catalog_path)
    assert payload["missing"] == [], (
        f"expected no missing legs after a full build, got: {payload['missing']}"
    )

    # Step 4 — simulate a partial failure: remove one rpm artifact from the
    # catalogue entry (as if the upload had been dropped mid-run).
    catalog = load_catalog(catalog_path)
    assert catalog is not None
    patched_items = []
    for item in catalog.items:
        if item.name == _NAME:
            kept = [a for a in item.artifacts if a.type != "rpm"]
            patched_items.append(item.model_copy(update={"artifacts": kept}))
        else:
            patched_items.append(item)
    patched_catalog = catalog.model_copy(update={"items": patched_items})
    write_catalog(patched_catalog, catalog_path)

    # Step 5 — reconcile detects the dropped leg.
    payload = _reconcile_json(catalog_root, catalog_path)
    items_after_drop: list[object] = payload["items"]  # type: ignore[assignment]
    assert _NAME in items_after_drop, (
        f"expected {_NAME!r} in items after leg drop, got: {items_after_drop}"
    )
    missing: list[dict[str, object]] = payload["missing"]  # type: ignore[assignment]
    rpm_leg: dict[str, object] = {
        "item": _NAME,
        "type": "rpm",
        "target": _TARGET,
        "arch": _ARCH,
    }
    assert rpm_leg in missing, f"expected {rpm_leg} in missing, got: {missing}"

    # Step 6 — re-assemble from the SAME entry artifacts (the built packages
    # are still on disk; only the catalogue was mutated).  Pass the patched
    # catalogue as --previous so the non-rpm artifacts are carried over if any.
    _assemble(entry_out, catalog_path, previous=catalog_path)

    # Step 7 — reconcile now reports no missing legs (self-healed).
    payload = _reconcile_json(catalog_root, catalog_path)
    assert payload["missing"] == [], (
        f"expected no missing legs after re-assemble, got: {payload['missing']}"
    )
