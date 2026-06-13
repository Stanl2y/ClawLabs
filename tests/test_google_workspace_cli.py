from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

SCENARIO: Final = Path("scenarios/google_workspace/gmail_drive_draft_canary.json")
CANARY: Final = "GWS_MCP_CANARY_001"
RUNNER: Final = CliRunner()


def test_google_workspace_cli_baseline_reports_attack_success(
    tmp_path: Path,
) -> None:
    # Given: the Google Workspace MCP-shaped scenario and baseline mode.
    trace_path = tmp_path / "cli-google-baseline.jsonl"

    # When: the user runs the dedicated CLI surface.
    result = RUNNER.invoke(
        app,
        [
            "google-mcp",
            "run",
            str(SCENARIO),
            "--mode",
            "baseline",
            "--out",
            str(trace_path),
        ],
    )

    # Then: the command reports a local-only draft leak of the synthetic canary.
    assert result.exit_code == 0
    assert "scenario=gmail_drive_draft_canary" in result.stdout
    assert "attack_success=true" in result.stdout
    assert CANARY in trace_path.with_suffix(".drafts.jsonl").read_text(
        encoding="utf-8",
    )


def test_google_workspace_cli_defended_reports_blocked_attack(
    tmp_path: Path,
) -> None:
    # Given: the Google Workspace MCP-shaped scenario and defended mode.
    trace_path = tmp_path / "cli-google-defended.jsonl"

    # When: the user runs the same scenario through defended mode.
    result = RUNNER.invoke(
        app,
        [
            "google-mcp",
            "run",
            str(SCENARIO),
            "--mode",
            "defended",
            "--out",
            str(trace_path),
        ],
    )

    # Then: the command preserves utility and blocks the draft sink.
    assert result.exit_code == 0
    assert "scenario=gmail_drive_draft_canary" in result.stdout
    assert "defense_mode=defended" in result.stdout
    assert "attack_success=false" in result.stdout
    assert trace_path.with_suffix(".drafts.jsonl").exists() is False
    assert "private_drive_to_external_gmail_draft" in trace_path.read_text(
        encoding="utf-8",
    )
