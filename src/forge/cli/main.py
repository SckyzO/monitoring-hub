"""Root Click group for the `mh` command."""

from __future__ import annotations

import click

from forge import __version__


@click.group(name="mh")
@click.version_option(version=__version__, prog_name="mh")
def cli() -> None:
    """monitoring-hub forge — build monitoring artifacts from manifests."""


if __name__ == "__main__":
    cli()
