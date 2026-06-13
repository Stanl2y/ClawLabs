from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

RUNNER: Final = CliRunner()


def test_lab_run_scenario_pack_generates_aggregate_summary(tmp_path: Path) -> None:
    # When: the scenario-pack runner executes every final-demo scenario.
    result = RUNNER.invoke(
        app,
        ["lab", "run-scenario-pack", "--out-dir", str(tmp_path), "--json"],
    )

    # Then: the aggregate summary reports every scenario as successful.
    assert result.exit_code == 0
    summary = (tmp_path / "scenario-pack-summary.json").read_text(encoding="utf-8")
    assert '"overall_success": true' in summary
    for scenario_id in (
        "google_workspace_canary",
        "memory_poisoning",
        "shopping_tool_description_poisoning",
        "rag_search_poisoning",
        "tool_use_confusion",
    ):
        assert scenario_id in summary

