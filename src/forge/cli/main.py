"""Root Click group for the `mh` command and its subcommands (spec §11)."""

from __future__ import annotations

import json as jsonlib
import sys
from pathlib import Path

import click

from forge import __version__
from forge.catalog.builder import build_catalog, load_catalog, write_catalog
from forge.cli._context import iter_manifest_paths, resolve_catalog_root
from forge.domain.catalog import CatalogEntry
from forge.domain.errors import ForgeError
from forge.domain.manifest import parse_manifest
from forge.fetch.http import HttpxDownloader
from forge.kinds.base import BuildContext
from forge.kinds.registry import discover, get_producer
from forge.packaging.runner import SubprocessRunner
from forge.sources.resolver import load_yaml_mapping, resolve_manifest, resolve_manifest_path

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
def validate(
    ref: str | None, catalog_root: str | None, validate_all: bool, as_json: bool
) -> None:
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
            jsonlib.dumps(
                [{"item": n, "ok": e is None, "error": e} for n, e in results], indent=2
            )
        )
    else:
        for name, err in failures:
            click.echo(f"FAIL {name}: {err}")
        click.echo(f"{len(results) - len(failures)}/{len(results)} valid")

    if failures:
        sys.exit(1)


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


def _build_context(work_dir: Path, sign_key: str | None) -> BuildContext:
    return BuildContext(
        work_dir=work_dir,
        downloader=HttpxDownloader(),
        runner=SubprocessRunner(),
        signing_key_id=sign_key,
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
def build(
    ref: str,
    catalog_root: str | None,
    sets: tuple[str, ...],
    overlay: Path | None,
    sign_key: str | None,
    work_dir: Path,
) -> None:
    """Build one item's artifacts locally (REF = catalogue name or manifest path)."""
    discover()
    root = resolve_catalog_root(catalog_root)
    manifest = resolve_manifest(ref, catalog_root=root, overlay_path=overlay, sets=sets)
    ctx = _build_context(work_dir, sign_key)
    result = get_producer(manifest.kind).build(manifest, ctx)
    for art in result.artifacts:
        click.echo(
            f"{art.type}\t{art.target or '-'}\t{art.arch or '-'}\t"
            f"{art.sha256[:12]}\tsigned={art.signed}"
        )
    click.echo(f"built {len(result.artifacts)} artifact(s) for {manifest.name}")


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
def catalog_build(
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

    ctx = _build_context(work_dir, sign_key)
    entries: list[CatalogEntry] = []
    for ref in item_refs:
        manifest = resolve_manifest(ref, catalog_root=root)
        entries.append(get_producer(manifest.kind).build(manifest, ctx).entry)

    prior = load_catalog(previous) if previous is not None else None
    result = build_catalog(entries, previous=prior)
    write_catalog(result, output)
    click.echo(f"wrote {len(result.items)} item(s) to {output}")


if __name__ == "__main__":
    cli()
