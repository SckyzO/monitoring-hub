"""
Example of how to integrate logging into builder.py

This file shows the pattern - the actual builder.py should be updated similarly.
Replace click.echo() with logger.info/error/warning as appropriate.
"""

from core.config.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


def example_function(url: str, b_name: str, member_names: list) -> None:
    """Example showing logging usage."""
    # Instead of: click.echo(f"Downloading {url}...")
    logger.info("Downloading %s...", url)

    try:
        # Some operation that might fail
        pass
    except Exception as e:
        # Instead of: click.echo(f"Error: {e}", err=True)
        logger.error("Failed to download: %s", e)

    # Instead of: click.echo(f"Warning: Binary '{b_name}' not found.")
    logger.warning("Binary '%s' not found in archive", b_name)

    # Debug information (only shown with --verbose or DEBUG level)
    logger.debug("Archive members: %s", member_names)


# To use in CLI commands with click:
# @click.command()
# @click.option('--verbose', is_flag=True, help='Enable debug logging')
# def build(verbose):
#     from core.config.logging import setup_logging
#     level = logging.DEBUG if verbose else logging.INFO
#     setup_logging(level=level)
#     logger = get_logger(__name__)
#     logger.info("Starting build process")
