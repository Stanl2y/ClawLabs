from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

RUNNER: Final = CliRunner()


def test_cli_help_shows_project_description() -> None:
    # Given: the AgentSec Lab CLI application.
    # When: the user asks for help.
    result = RUNNER.invoke(app, ["--help"])

    # Then: the CLI renders a successful help page with the project description.
    assert result.exit_code == 0
    assert "AgentSec Lab" in result.stdout
    assert "agentic AI security benchmark" in result.stdout


def test_cli_version_prints_current_version() -> None:
    # Given: the AgentSec Lab CLI application.
    # When: the user asks for the version.
    result = RUNNER.invoke(app, ["--version"])

    # Then: the CLI prints the current package version.
    assert result.exit_code == 0
    assert "agentsec-lab 0.1.0" in result.stdout
