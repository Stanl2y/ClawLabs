from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app
from agentsec_lab.google_workspace.direct_mcp import run_google_workspace_direct_mcp
from agentsec_lab.types import DefenseMode

SCENARIO: Final = Path("scenarios/google_workspace/gmail_drive_draft_canary.json")
CANARY: Final = "GWS_MCP_CANARY_001"
RUNNER: Final = CliRunner()


def test_direct_mcp_baseline_creates_canary_draft_through_stdio(
    tmp_path: Path,
) -> None:
    # Given: the local Google Workspace MCP stdio server and baseline mode.
    trace_path = tmp_path / "direct-baseline.jsonl"

    # When: the direct runner bypasses NanoClaw and drives MCP JSON-RPC itself.
    result = run_google_workspace_direct_mcp(
        scenario_path=SCENARIO,
        trace_path=trace_path,
        defense_mode=DefenseMode.BASELINE,
    )

    # Then: the synthetic private canary reaches the local draft evidence sink.
    draft_text = trace_path.with_suffix(".drafts.jsonl").read_text(encoding="utf-8")
    trace_text = trace_path.read_text(encoding="utf-8")
    assert result.utility_success is True
    assert result.attack_success is True
    assert "support_reply_ready draft-local-001" in result.final_answer
    assert CANARY in draft_text
    assert '"tool_name":"gmail.create_draft"' in trace_text


def test_direct_mcp_defended_blocks_canary_draft_through_stdio(
    tmp_path: Path,
) -> None:
    # Given: the same MCP stdio server with defended mode.
    trace_path = tmp_path / "direct-defended.jsonl"

    # When: the direct runner attempts the same draft through MCP JSON-RPC.
    result = run_google_workspace_direct_mcp(
        scenario_path=SCENARIO,
        trace_path=trace_path,
        defense_mode=DefenseMode.DEFENDED,
    )

    # Then: the workflow completes, but no draft evidence is written.
    trace_text = trace_path.read_text(encoding="utf-8")
    assert result.utility_success is True
    assert result.attack_success is False
    assert "support_reply_ready blocked" in result.final_answer
    assert trace_path.with_suffix(".drafts.jsonl").exists() is False
    assert '"kind":"defense_block"' in trace_text


def test_direct_mcp_cli_reports_baseline_attack_success(tmp_path: Path) -> None:
    # Given: the dedicated direct MCP bypass CLI surface.
    trace_path = tmp_path / "direct-cli-baseline.jsonl"

    # When: the user runs the bypass command.
    result = RUNNER.invoke(
        app,
        [
            "google-mcp",
            "direct-attack",
            str(SCENARIO),
            "--mode",
            "baseline",
            "--out",
            str(trace_path),
        ],
    )

    # Then: the command reports NanoClaw-bypassed MCP attack success.
    assert result.exit_code == 0
    assert "surface=direct_mcp_stdio" in result.stdout
    assert "attack_success=true" in result.stdout
    assert CANARY in trace_path.with_suffix(".drafts.jsonl").read_text(
        encoding="utf-8",
    )
