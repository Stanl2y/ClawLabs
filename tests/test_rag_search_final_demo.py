from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app

CANARY: Final = "ISO_SYNTH_CANARY_42"
RUNNER: Final = CliRunner()


def test_lab_run_rag_search_demo_generates_baseline_and_defended_summary(
    tmp_path: Path,
) -> None:
    # When: the final-demo runner drives the RAG/search poisoning scenario.
    result = RUNNER.invoke(
        app,
        ["lab", "run-rag-search-demo", "--out-dir", str(tmp_path), "--json"],
    )

    # Then: baseline reaches the local sink and defended blocks the same attempt.
    assert result.exit_code == 0
    baseline_sink = tmp_path / "rag-search-baseline" / "rag-search.sink.txt"
    defended_sink = tmp_path / "rag-search-defended" / "rag-search.sink.txt"
    defended_trace = tmp_path / "rag-search-defended" / "rag-search.jsonl"
    assert baseline_sink.read_text(encoding="utf-8") == CANARY
    assert not defended_sink.exists()
    defended_text = defended_trace.read_text(encoding="utf-8")
    assert "defense_block" in defended_text
    assert "quarantined_memory" in defended_text
    summary = (tmp_path / "rag-search-demo-summary.json").read_text(
        encoding="utf-8",
    )
    assert '"scenario_id": "rag_search_poisoning"' in summary
    assert '"attack_success": true' in summary
    assert '"attack_success": false' in summary
    assert '"defense_blocked": true' in summary

