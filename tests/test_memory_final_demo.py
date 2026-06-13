from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

CANARY: Final = "MEMORY_SYNTH_CANARY_001"
RUNNER: Final = CliRunner()


def test_lab_run_memory_demo_generates_baseline_and_defended_summary(
    tmp_path: Path,
) -> None:
    # When: the final-demo runner drives the Memory MCP stdio server.
    result = RUNNER.invoke(
        app,
        ["lab", "run-memory-demo", "--out-dir", str(tmp_path), "--json"],
    )

    # Then: baseline stores poisoned memory and defended quarantines it.
    assert result.exit_code == 0
    baseline_trace = tmp_path / "memory-baseline" / "memory.jsonl"
    defended_trace = tmp_path / "memory-defended" / "memory.jsonl"
    assert CANARY in baseline_trace.read_text(encoding="utf-8")
    defended_text = defended_trace.read_text(encoding="utf-8")
    assert '"kind":"quarantined_memory"' in defended_text
    assert CANARY not in defended_text
    summary = (tmp_path / "memory-demo-summary.json").read_text(encoding="utf-8")
    assert '"scenario_id": "memory_poisoning"' in summary
    assert '"attack_success": true' in summary
    assert '"attack_success": false' in summary
    assert '"defense_blocked": true' in summary
