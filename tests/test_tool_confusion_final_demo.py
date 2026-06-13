from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

CANARY: Final = "ISO_SYNTH_CANARY_42"
RUNNER: Final = CliRunner()


def test_lab_run_tool_confusion_demo_generates_baseline_and_defended_summary(
    tmp_path: Path,
) -> None:
    # When: the final-demo runner drives the tool-use confusion scenario.
    result = RUNNER.invoke(
        app,
        ["lab", "run-tool-confusion-demo", "--out-dir", str(tmp_path), "--json"],
    )

    # Then: baseline follows the ambiguous callback and defended blocks the sink.
    assert result.exit_code == 0
    baseline_sink = tmp_path / "tool-confusion-baseline" / "tool-confusion.sink.txt"
    defended_sink = tmp_path / "tool-confusion-defended" / "tool-confusion.sink.txt"
    defended_trace = tmp_path / "tool-confusion-defended" / "tool-confusion.jsonl"
    assert baseline_sink.read_text(encoding="utf-8") == CANARY
    assert not defended_sink.exists()
    assert "defense_block" in defended_trace.read_text(encoding="utf-8")
    summary = (tmp_path / "tool-confusion-demo-summary.json").read_text(
        encoding="utf-8",
    )
    assert '"scenario_id": "tool_use_confusion"' in summary
    assert '"attack_success": true' in summary
    assert '"attack_success": false' in summary
    assert '"defense_blocked": true' in summary

