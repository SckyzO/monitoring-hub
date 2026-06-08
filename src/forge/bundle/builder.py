"""Offline bundle orchestration (spec §5.6): resolve → fetch → assemble → pack.

The only deliverable is the ``.tar.gz``. ``inputs/`` (fetched blobs) and ``tree/``
(the assembled bundle) are siblings under ``staging``; only ``tree/`` is packed,
so the raw blobs never leak into the archive.
"""

from __future__ import annotations

from pathlib import Path

from forge.bundle.archive import pack
from forge.bundle.assemble import assemble_bundle, write_sha256sums
from forge.bundle.images import ImageSource, save_images
from forge.bundle.resolver import resolve_artifacts
from forge.bundle.source import ArtifactSource
from forge.domain.catalog import Catalog
from forge.domain.recipe import BundleRecipe
from forge.packaging.runner import CommandRunner


def build_bundle(  # noqa: PLR0913 — orchestrator with explicit keyword-only I/O params
    *,
    recipe: BundleRecipe,
    catalog: Catalog,
    source: ArtifactSource,
    staging: Path,
    out: Path,
    key_id: str | None = None,
    public_key: Path | None = None,
    image_source: ImageSource | None = None,
    image_arches: list[str] | None = None,
    runner: CommandRunner,
) -> Path:
    """Resolve the recipe against the catalogue, fetch every artefact via ``source``,
    assemble the offline tree, and pack it into ``out``. Returns the archive path.

    With ``image_source`` set, each item's OCI image is saved into ``tree/images/``
    as per-arch docker-archive tarballs and folded into ``SHA256SUMS``."""
    resolved = resolve_artifacts(recipe, catalog, include_images=image_source is not None)
    inputs_dir = staging / "inputs"
    tree = staging / "tree"
    for art in resolved:
        if art.artifact.type == "docker-image":
            continue  # images are saved via image_source, not fetched as blobs
        source.fetch(art, inputs_dir / art.filename)
    assemble_bundle(
        resolved,
        inputs_dir=inputs_dir,
        staging=tree,
        recipe=recipe,
        key_id=key_id,
        public_key=public_key,
        with_images=image_source is not None,
        runner=runner,
    )
    if image_source is not None:
        save_images(resolved, dest_dir=tree / "images", source=image_source, arches=image_arches)
        write_sha256sums(tree)
    return pack(tree, out, runner=runner)
