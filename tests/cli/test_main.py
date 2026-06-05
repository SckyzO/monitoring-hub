from click.testing import CliRunner

from forge import __version__
from forge.cli.main import cli


def test_version_reports_package_version() -> None:
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help_lists_the_program_name() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage: mh" in result.output
