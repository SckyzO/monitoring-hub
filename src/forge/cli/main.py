"""Root Click group for the `mh` command and its subcommands (spec §11)."""

from __future__ import annotations

import json as jsonlib

import click

from forge import __version__
from forge.cli._context import iter_manifest_paths, resolve_catalog_root
from forge.domain.errors import ForgeError
from forge.domain.manifest import parse_manifest
from forge.sources.resolver import load_yaml_mapping

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


if __name__ == "__main__":
    cli()
