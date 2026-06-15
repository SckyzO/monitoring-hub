"""Root Click group for the `mh` command and its subcommands (spec §11)."""

from __future__ import annotations

import json as jsonlib
import shutil
import sys
import tempfile
from pathlib import Path

import click

from forge import __version__
from forge.bundle.builder import build_bundle
from forge.bundle.images import ImageSource, LocalImageSource, RegistryImageSource
from forge.bundle.resolver import load_recipe, recipe_from_selection
from forge.bundle.source import ArtifactSource, LocalDirSource, ReleasesFetcher
from forge.catalog.builder import assemble_catalog, build_catalog, load_catalog, write_catalog
from forge.catalog.entries import load_entries, write_entry
from forge.cli._context import iter_manifest_paths, resolve_catalog_root
from forge.detect.base import DetectedVersion
from forge.detect.bump import bump_manifest
from forge.detect.reconcile import missing_legs
from forge.detect.registry import discover as discover_sources
from forge.detect.watch import detect_all
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import ForgeError
from forge.domain.manifest import parse_manifest
from forge.fetch.http import HttpxDownloader
from forge.kinds.base import BuildContext
from forge.kinds.registry import discover, get_producer
from forge.packaging.runner import SubprocessRunner
from forge.publish.oci import OciPublisher
from forge.publish.releases import GitHubReleasesPublisher
from forge.repo.builder import build_distribution
from forge.sources.resolver import load_yaml_mapping, resolve_manifest, resolve_manifest_path

_DEFAULT_PACKAGE_BASE_URL = "https://github.com/SckyzO/monitoring-hub/releases/download"
_DEFAULT_PAGES_BASE_URL = "https://sckyzo.github.io/monitoring-hub"
_DEFAULT_OCI_REGISTRY = "ghcr.io/sckyzo/monitoring-hub"
_DEFAULT_RELEASES_REPO = "SckyzO/monitoring-hub"

_catalog_root_option = click.option(
    "--catalog-root",
    "catalog_root",
    default=None,
    help="Catalogue data root (default: $FORGE_CATALOG_ROOT or ./catalog).",
)


@click.group(name="mh")
@click.version_option(version=__version__, prog_name="mh")
def cli() -> None:
    """monitoring-hub forge — build monitoring artifacts from manifests."""


@cli.command(name="list")
@_catalog_root_option
@click.option("--kind", default=None, help="Only list items of this kind (e.g. exporter).")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def list_items(catalog_root: str | None, kind: str | None, as_json: bool) -> None:
    """List catalogue items (name, kind, version, category)."""
    root = resolve_catalog_root(catalog_root)
    rows: list[dict[str, str]] = []
    for path in iter_manifest_paths(root, kind=kind):
        manifest = parse_manifest(load_yaml_mapping(path))
        rows.append(
            {
                "name": manifest.name,
                "kind": manifest.kind,
                "version": manifest.version,
                "category": manifest.category,
            }
        )
    if as_json:
        click.echo(jsonlib.dumps(rows, indent=2))
        return
    for row in rows:
        click.echo(f"{row['name']}\t{row['kind']}\t{row['version']}\t{row['category']}")


def _validate_path(path: Path) -> str | None:
    """Validate one manifest file: schema then producer semantics.

    Returns ``None`` on success or a human-readable error string. Producers must
    be discovered (registered) before calling.
    """
    try:
        manifest = parse_manifest(load_yaml_mapping(path))
        get_producer(manifest.kind).validate(manifest)
    except ForgeError as exc:
        return str(exc)
    return None


@cli.command()
@click.argument("ref", required=False)
@_catalog_root_option
@click.option("--all", "validate_all", is_flag=True, help="Validate every catalogue item.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def validate(ref: str | None, catalog_root: str | None, validate_all: bool, as_json: bool) -> None:
    """Validate one item (REF) or the whole catalogue (--all).

    Aggregates every failure rather than stopping at the first (spec §14) and
    exits non-zero if any item is invalid.
    """
    discover()
    root = resolve_catalog_root(catalog_root)

    targets: list[tuple[str, Path]]
    if validate_all:
        targets = [(p.parent.name, p) for p in iter_manifest_paths(root)]
    elif ref:
        targets = [(ref, resolve_manifest_path(ref, catalog_root=root))]
    else:
        raise click.UsageError("provide an item REF or --all")

    results = [(name, _validate_path(path)) for name, path in targets]
    failures = [(name, err) for name, err in results if err is not None]

    if as_json:
        click.echo(
            jsonlib.dumps([{"item": n, "ok": e is None, "error": e} for n, e in results], indent=2)
        )
    else:
        for name, err in failures:
            click.echo(f"FAIL {name}: {err}")
        click.echo(f"{len(results) - len(failures)}/{len(results)} valid")

    if failures:
        sys.exit(1)


@cli.command()
@_catalog_root_option
@click.option("--kind", default=None, help="Only watch items of this kind (e.g. exporter).")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def watch(catalog_root: str | None, kind: str | None, as_json: bool) -> None:
    """Detect outdated catalogue items against their upstreams (read-only)."""
    discover_sources()
    root = resolve_catalog_root(catalog_root)
    manifests = [
        parse_manifest(load_yaml_mapping(path)) for path in iter_manifest_paths(root, kind=kind)
    ]
    detected: list[DetectedVersion] = detect_all(manifests, runner=SubprocessRunner())

    if as_json:
        click.echo(
            jsonlib.dumps(
                [
                    {
                        "item": d.item,
                        "kind": d.kind,
                        "current": d.current,
                        "latest": d.latest,
                        "latest_raw": d.latest_raw,
                        "source_type": d.source_type,
                        "outdated": d.outdated,
                    }
                    for d in detected
                ],
                indent=2,
            )
        )
        return
    for d in detected:
        flag = "OUTDATED" if d.outdated else "ok"
        click.echo(f"{d.item}\t{d.kind}\t{d.current}\t→ {d.latest}\t{flag}")


@cli.command()
@click.argument("ref")
@click.option("--to", "to", required=True, help="New version to write (verbatim upstream tag).")
@_catalog_root_option
def bump(ref: str, to: str, catalog_root: str | None) -> None:
    """Set an item's manifest version (validated, atomic; REF = name or path)."""
    root = resolve_catalog_root(catalog_root)
    try:
        path = resolve_manifest_path(ref, catalog_root=root)
        manifest = bump_manifest(path, to=to)
    except ForgeError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"bumped {manifest.name} to {manifest.version}")


_set_option = click.option(
    "--set",
    "sets",
    multiple=True,
    metavar="PATH=VALUE",
    help="Override a manifest field by path (repeatable).",
)
_overlay_option = click.option(
    "--overlay",
    "overlay",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Partial overlay YAML deep-merged over the manifest.",
)


def _build_context(
    work_dir: Path, sign_key: str | None, manifest_dir: Path | None = None
) -> BuildContext:
    return BuildContext(
        work_dir=work_dir,
        downloader=HttpxDownloader(),
        runner=SubprocessRunner(),
        signing_key_id=sign_key,
        manifest_dir=manifest_dir,
    )


@cli.command()
@click.argument("ref")
@_catalog_root_option
@_set_option
@_overlay_option
@click.option("--sign-key", "sign_key", default=None, help="GPG key id to sign packages.")
@click.option(
    "--work-dir",
    "work_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("build"),
    show_default=True,
    help="Working directory for downloads and produced artifacts.",
)
@click.option(
    "--entry-out",
    "entry_out",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Directory to write this item's entry.json (for mh catalog assemble).",
)
def build(  # noqa: PLR0913 — Click options map one-to-one to parameters
    ref: str,
    catalog_root: str | None,
    sets: tuple[str, ...],
    overlay: Path | None,
    sign_key: str | None,
    work_dir: Path,
    entry_out: Path | None,
) -> None:
    """Build one item's artifacts locally (REF = catalogue name or manifest path)."""
    discover()
    root = resolve_catalog_root(catalog_root)
    manifest_path = resolve_manifest_path(ref, catalog_root=root)
    manifest = resolve_manifest(ref, catalog_root=root, overlay_path=overlay, sets=sets)
    ctx = _build_context(work_dir, sign_key, manifest_dir=manifest_path.parent)
    result = get_producer(manifest.kind).build(manifest, ctx)
    for art in result.artifacts:
        click.echo(
            f"{art.type}\t{art.target or '-'}\t{art.arch or '-'}\t"
            f"{art.sha256[:12]}\tsigned={art.signed}"
        )
    if entry_out is not None:
        write_entry(result.entry, entry_out)
    click.echo(f"built {len(result.artifacts)} artifact(s) for {manifest.name}")


@cli.command()
@click.argument("item")
@_catalog_root_option
@click.option(
    "--dest",
    "dest",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Directory to copy the manifest into (as <dest>/<item>/manifest.yaml).",
)
def pull(item: str, catalog_root: str | None, dest: Path) -> None:
    """Copy a catalogue manifest locally for customization.

    Fetching from a remote published catalogue is deferred to SP2; for now this
    copies from the in-repo catalogue root.
    """
    root = resolve_catalog_root(catalog_root)
    try:
        source = resolve_manifest_path(item, catalog_root=root)
    except ForgeError as exc:
        raise click.ClickException(str(exc)) from exc
    target_dir = dest / source.parent.name
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    shutil.copy2(source, target)
    click.echo(f"pulled {item} to {target}")


@cli.group()
def catalog() -> None:
    """Catalogue operations (assemble catalog.json)."""


@catalog.command(name="build")
@click.argument("refs", nargs=-1)
@_catalog_root_option
@click.option("--all", "build_all", is_flag=True, help="Build every catalogue item.")
@click.option(
    "--previous",
    "previous",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Previous catalog.json to diff for new/updated flags.",
)
@click.option(
    "--output",
    "output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("catalog.json"),
    show_default=True,
    help="Where to write the assembled catalog.json.",
)
@click.option("--sign-key", "sign_key", default=None, help="GPG key id to sign packages.")
@click.option(
    "--work-dir",
    "work_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("build"),
    show_default=True,
    help="Working directory for downloads and produced artifacts.",
)
def catalog_build(  # noqa: PLR0913 — Click options map one-to-one to parameters
    refs: tuple[str, ...],
    catalog_root: str | None,
    build_all: bool,
    previous: Path | None,
    output: Path,
    sign_key: str | None,
    work_dir: Path,
) -> None:
    """Build items then assemble their CatalogEntry objects into catalog.json."""
    discover()
    root = resolve_catalog_root(catalog_root)
    if build_all:
        item_refs = [str(p) for p in iter_manifest_paths(root)]
    elif refs:
        item_refs = list(refs)
    else:
        raise click.UsageError("provide one or more REFS or --all")

    entries: list[CatalogEntry] = []
    for ref in item_refs:
        # Each item resolves its own manifest_dir so the producer can stage that
        # item's assets/ and resolve its custom docker.dockerfile (one ctx each).
        manifest_path = resolve_manifest_path(ref, catalog_root=root)
        manifest = resolve_manifest(ref, catalog_root=root)
        ctx = _build_context(work_dir, sign_key, manifest_dir=manifest_path.parent)
        entries.append(get_producer(manifest.kind).build(manifest, ctx).entry)

    prior = load_catalog(previous) if previous is not None else None
    result = build_catalog(entries, previous=prior)
    write_catalog(result, output)
    click.echo(f"wrote {len(result.items)} item(s) to {output}")


@catalog.command(name="assemble")
@click.option(
    "--entries",
    "entries_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory of per-item entry.json files (from mh build --entry-out).",
)
@click.option(
    "--previous",
    "previous",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Previous catalog.json to merge over (unbuilt items are kept).",
)
@click.option(
    "--output",
    "output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("catalog.json"),
    show_default=True,
    help="Where to write the assembled catalog.json.",
)
def catalog_assemble(entries_dir: Path, previous: Path | None, output: Path) -> None:
    """Join per-item entry.json files into catalog.json, merging over a previous one."""
    entries = load_entries(entries_dir)
    prior = load_catalog(previous) if previous is not None else None
    result = assemble_catalog(entries, previous=prior)
    write_catalog(result, output)
    click.echo(f"assembled {len(result.items)} item(s) into {output}")


@catalog.command(name="reconcile")
@_catalog_root_option
@click.option(
    "--catalog",
    "catalog_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Published catalog.json to diff against (omit to treat everything as missing).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def catalog_reconcile(catalog_root: str | None, catalog_path: Path | None, as_json: bool) -> None:
    """Report missing = expected(manifest matrix) - present(catalog) legs (spec §7).

    ``--json`` emits ``{"missing": [{item,type,target,arch}], "items": [names]}``;
    the reconcile workflow drives its build matrix from ``items`` and renders
    ``missing`` into the run's step summary. No writes.
    """
    discover()
    root = resolve_catalog_root(catalog_root)
    manifests = [parse_manifest(load_yaml_mapping(p)) for p in iter_manifest_paths(root)]
    catalog = load_catalog(catalog_path) if catalog_path is not None else None
    legs = missing_legs(manifests, catalog)
    items = sorted({leg.item for leg in legs})

    if as_json:
        click.echo(
            jsonlib.dumps(
                {
                    "missing": [
                        {"item": x.item, "type": x.type, "target": x.target, "arch": x.arch}
                        for x in legs
                    ],
                    "items": items,
                },
                indent=2,
            )
        )
        return

    if not legs:
        click.echo("all legs present")
        return
    for leg in legs:
        click.echo(f"{leg.item}\t{leg.type}\t{leg.target or '-'}\t{leg.arch or '-'}")
    click.echo(f"{len(legs)} missing leg(s) across {len(items)} item(s)")


@cli.group()
def repo() -> None:
    """Repository operations (assemble signed apt/yum trees)."""


@repo.command(name="build")
@click.option(
    "--catalog",
    "catalog_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("catalog.json"),
    show_default=True,
    help="catalog.json to read (and re-emit with populated Artifact.url).",
)
@click.option(
    "--packages",
    "packages_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("dist"),
    show_default=True,
    help="Directory tree holding the built .rpm/.deb (from mh build).",
)
@click.option(
    "--dashboards",
    "dashboards_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("dist/dashboards"),
    show_default=True,
    help="Directory holding the built dashboard JSON files.",
)
@click.option(
    "--out",
    "public_out",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("public"),
    show_default=True,
    help="Pages metadata tree to assemble (repodata, dashboards, catalog.json).",
)
@click.option(
    "--release-out",
    "release_out",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("release"),
    show_default=True,
    help="Releases staging tree (rpm-* / apt-* asset dirs).",
)
@click.option(
    "--package-base-url",
    "package_base_url",
    default=_DEFAULT_PACKAGE_BASE_URL,
    show_default=True,
    help="Base URL where package blobs are hosted (GitHub Releases by default).",
)
@click.option(
    "--pages-base-url",
    "pages_base_url",
    default=_DEFAULT_PAGES_BASE_URL,
    show_default=True,
    help="Base URL of the Pages site (for dashboard download URLs).",
)
@click.option("--sign", "sign", is_flag=True, help="Sign repo metadata (requires --key-id).")
@click.option("--key-id", "key_id", default=None, help="GPG key id used to sign metadata.")
@click.option(
    "--merge",
    "merge",
    is_flag=True,
    help="Incremental: merge built items into the published index (spec §4).",
)
@click.option(
    "--public-key",
    "public_key",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="GPG public key to publish on Pages (RPM-GPG-KEY + apt/monitoring-hub.asc).",
)
def repo_build(  # noqa: PLR0913 — Click options map one-to-one to parameters
    catalog_path: Path,
    packages_dir: Path,
    dashboards_dir: Path,
    public_out: Path,
    release_out: Path,
    package_base_url: str,
    pages_base_url: str,
    sign: bool,
    key_id: str | None,
    public_key: Path | None,
    merge: bool,
) -> None:
    """Assemble the Pages (--out) and Releases (--release-out) distribution trees."""
    if sign and key_id is None:
        raise click.UsageError("--sign requires --key-id")
    catalog = load_catalog(catalog_path)
    if catalog is None:
        raise click.ClickException(f"catalog not found: {catalog_path}")
    result = build_distribution(
        catalog=catalog,
        packages_dir=packages_dir,
        dashboards_dir=dashboards_dir,
        public_out=public_out,
        release_out=release_out,
        package_base_url=package_base_url,
        pages_base_url=pages_base_url,
        key_id=key_id if sign else None,
        public_key=public_key,
        merge=merge,
        downloader=HttpxDownloader() if merge else None,
        runner=SubprocessRunner(),
    )
    click.echo(f"assembled {len(result.items)} item(s) into {public_out} and {release_out}")


@cli.command()
@click.option("--oci", "oci", is_flag=True, help="Build + push multi-arch OCI images.")
@click.option(
    "--registry",
    "registries",
    multiple=True,
    default=(_DEFAULT_OCI_REGISTRY,),
    show_default=True,
    help="OCI registry namespace to push images to (repeatable; pushed once-per-build).",
)
@click.option(
    "--contexts",
    "contexts_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("dist/docker"),
    show_default=True,
    help="Directory of <name>/ docker build contexts (from mh build).",
)
@click.option(
    "--catalog",
    "catalog_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("catalog.json"),
    show_default=True,
    help="catalog.json supplying each image's version.",
)
@click.option(
    "--releases",
    "releases_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Staging tree of rpm-*/apt-* tag dirs to upload to GitHub Releases.",
)
@click.option(
    "--repo",
    "repo",
    default=_DEFAULT_RELEASES_REPO,
    show_default=True,
    help="owner/name of the GitHub repo whose Releases receive the assets.",
)
def publish(  # noqa: PLR0913 — Click options map one-to-one to parameters
    oci: bool,
    registries: tuple[str, ...],
    contexts_dir: Path,
    catalog_path: Path,
    releases_dir: Path | None,
    repo: str,
) -> None:
    """Publish built artifacts to remote hosts (OCI → GHCR, releases → GitHub)."""
    if not oci and releases_dir is None:
        raise click.UsageError("nothing to publish: pass --oci and/or --releases")
    runner = SubprocessRunner()
    if oci:
        catalog = load_catalog(catalog_path)
        if catalog is None:
            raise click.ClickException(f"catalog not found: {catalog_path}")
        versions = {item.name: item.version for item in catalog.items}
        OciPublisher(registries=registries, versions=versions, runner=runner).publish(contexts_dir)
        click.echo(f"published {len(versions)} image(s) to {', '.join(registries)}")
    if releases_dir is not None:
        GitHubReleasesPublisher(repo=repo, runner=runner).publish(releases_dir)
        click.echo(f"published release assets from {releases_dir} to {repo}")


def _split_csv(value: str | None) -> list[str] | None:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


@cli.command()
@click.option(
    "--recipe",
    "recipe_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Bundle recipe (YAML or JSON) describing the items to bundle.",
)
@click.option(
    "--item",
    "items",
    multiple=True,
    metavar="[KIND:]NAME[@VERSION]",
    help="Catalogue item to bundle (repeatable); synthesises a recipe.",
)
@click.option(
    "--target", "target", default=None, help="Comma-separated targets (e.g. el9,ubuntu-24.04)."
)
@click.option("--arch", "arch", default=None, help="Comma-separated arches (e.g. amd64,arm64).")
@click.option(
    "--catalog",
    "catalog_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("catalog.json"),
    show_default=True,
    help="catalog.json resolving item versions and artefacts.",
)
@click.option(
    "--packages",
    "packages_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Local mh-build tree to source blobs from (default: GitHub Releases).",
)
@click.option(
    "--repo",
    "repo",
    default=_DEFAULT_RELEASES_REPO,
    show_default=True,
    help="owner/name of the GitHub repo whose Releases hold the blobs.",
)
@click.option(
    "--images", "images", is_flag=True, help="Ship each item's OCI image (docker-archive)."
)
@click.option(
    "--build-images",
    "build_images",
    is_flag=True,
    help="Build images locally from contexts (buildah) instead of pulling the registry.",
)
@click.option(
    "--contexts",
    "contexts_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("dist/docker"),
    show_default=True,
    help="Directory of <name>/ docker build contexts (for --build-images).",
)
@click.option(
    "--image-arch", "image_arch", default=None, help="Comma-separated image arches (default: all)."
)
@click.option(
    "--registry",
    "registry",
    default=_DEFAULT_OCI_REGISTRY,
    show_default=True,
    help="OCI registry namespace to pull images from (for --images).",
)
@click.option(
    "--sign", "sign", is_flag=True, help="Sign repo metadata + recipe (requires --key-id)."
)
@click.option("--key-id", "key_id", default=None, help="GPG key id used to sign.")
@click.option(
    "--public-key",
    "public_key",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="GPG public key to ship in the bundle (RPM-GPG-KEY-monitoring-hub).",
)
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("bundle.tar.gz"),
    show_default=True,
    help="Output archive path.",
)
def bundle(  # noqa: PLR0913 — Click options map one-to-one to parameters
    recipe_path: Path | None,
    items: tuple[str, ...],
    target: str | None,
    arch: str | None,
    catalog_path: Path,
    packages_dir: Path | None,
    repo: str,
    images: bool,
    build_images: bool,
    contexts_dir: Path,
    image_arch: str | None,
    registry: str,
    sign: bool,
    key_id: str | None,
    public_key: Path | None,
    output: Path,
) -> None:
    """Build a self-contained offline bundle (.tar.gz) for air-gapped installs."""
    if bool(recipe_path) == bool(items):
        raise click.UsageError("exactly one of --recipe / --item must be given")
    if sign and key_id is None:
        raise click.UsageError("--sign requires --key-id")
    if recipe_path is not None and (target or arch):
        raise click.UsageError("--target/--arch only apply to --item; the recipe is authoritative")
    want_images = images or build_images
    if image_arch and not want_images:
        raise click.UsageError("--image-arch requires --images")

    catalog = load_catalog(catalog_path)
    if catalog is None:
        raise click.ClickException(f"catalog not found: {catalog_path}")

    try:
        if recipe_path is not None:
            recipe = load_recipe(recipe_path)
        else:
            recipe = recipe_from_selection(
                list(items), catalog, targets=_split_csv(target), arches=_split_csv(arch)
            )
    except ForgeError as exc:
        raise click.ClickException(str(exc)) from exc

    runner = SubprocessRunner()
    source: ArtifactSource = (
        LocalDirSource(packages_dir)
        if packages_dir is not None
        else ReleasesFetcher(repo=repo, runner=runner, downloader=HttpxDownloader())
    )
    image_source: ImageSource | None = None
    if want_images:
        image_source = (
            LocalImageSource(contexts_root=contexts_dir, runner=runner)
            if build_images
            else RegistryImageSource(registry=registry, runner=runner)
        )

    try:
        with tempfile.TemporaryDirectory(prefix="mh-bundle-") as staging:
            build_bundle(
                recipe=recipe,
                catalog=catalog,
                source=source,
                staging=Path(staging),
                out=output,
                key_id=key_id if sign else None,
                public_key=public_key,
                image_source=image_source,
                image_arches=_split_csv(image_arch),
                runner=runner,
            )
    except ForgeError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"wrote {output} ({len(recipe.items)} item(s))")


if __name__ == "__main__":
    cli()
