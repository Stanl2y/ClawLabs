from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

RUNNER: Final = CliRunner()


def test_lab_run_shopping_demo_generates_baseline_and_defended_summary(
    tmp_path: Path,
) -> None:
    # When: the final-demo runner drives the Shopping WebMCP stdio server.
    result = RUNNER.invoke(
        app,
        ["lab", "run-shopping-demo", "--out-dir", str(tmp_path), "--json"],
    )

    # Then: baseline records a mock order and defended records a pinned-surface block.
    assert result.exit_code == 0
    baseline_orders = tmp_path / "shopping-baseline" / "mock_orders.jsonl"
    defended_orders = tmp_path / "shopping-defended" / "mock_orders.jsonl"
    defended_blocks = tmp_path / "shopping-defended" / "shopping_policy_blocks.jsonl"
    assert "mock_order_created" in baseline_orders.read_text(encoding="utf-8")
    assert not defended_orders.exists()
    assert "tool_description_pinning_diff" in defended_blocks.read_text(
        encoding="utf-8",
    )
    summary = (tmp_path / "shopping-demo-summary.json").read_text(encoding="utf-8")
    assert '"scenario_id": "shopping_tool_description_poisoning"' in summary
    assert '"attack_success": true' in summary
    assert '"attack_success": false' in summary
    assert '"defense_blocked": true' in summary

