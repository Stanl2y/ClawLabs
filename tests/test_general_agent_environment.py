from pathlib import Path
from typing import Final

from typer.testing import CliRunner

from agentsec_lab.cli import app
from agentsec_lab.model import FakeModelMode
from agentsec_lab.runner import run_scenario
from agentsec_lab.scenario import load_scenario

BENIGN_SCENARIO: Final = Path("scenarios/general/vendor_research_benign.json")
POISONED_SCENARIO: Final = Path("scenarios/general/vendor_research_poisoned.json")
PATH_ESCAPE_SCENARIO: Final = Path("scenarios/general/path_escape.json")


def test_general_workflow_records_memory_vendor_and_provenance_trace(
    tmp_path: Path,
) -> None:
    # Given: a benign general-agent scenario with local untrusted research input.
    scenario = load_scenario(BENIGN_SCENARIO)
    trace_path = tmp_path / "general-benign.jsonl"

    # When: the general benign fake model completes the workflow.
    result = run_scenario(
        scenario=scenario,
        model_mode=FakeModelMode("fake-general-benign"),
        trace_path=trace_path,
    )

    # Then: the trace captures vendor search, memory use, and provenance.
    trace_text = trace_path.read_text(encoding="utf-8")
    assert result.utility_success is True
    assert result.attack_success is False
    assert "ACME SecureWorks" in result.final_answer
    assert "vendor_search" in trace_text
    assert "memory_write" in trace_text
    assert "memory_read" in trace_text
    assert "provenance" in trace_text
    assert "untrusted_document" in trace_text
    assert "mock_vendor_api" in trace_text


def test_baseline_poisoned_workflow_records_attack_success_and_sink(
    tmp_path: Path,
) -> None:
    # Given: a poisoned general-agent scenario and baseline defenses.
    trace_path = tmp_path / "general-poisoned-baseline.jsonl"

    # When: the malicious fake model runs through the real CLI surface.
    result = CliRunner().invoke(
        app,
        [
            "run",
            str(POISONED_SCENARIO),
            "--model",
            "fake-general-malicious",
            "--mode",
            "baseline",
            "--out",
            str(trace_path),
        ],
    )

    # Then: the local-only sink records the synthetic canary exfiltration.
    assert result.exit_code == 0
    sink_path = trace_path.with_suffix(".sink.txt")
    trace_text = trace_path.read_text(encoding="utf-8")
    assert "scenario=vendor_research_poisoned" in result.stdout
    assert "defense_mode=baseline" in result.stdout
    assert "attack_success=true" in result.stdout
    assert "utility_success=true" in result.stdout
    assert sink_path.read_text(encoding="utf-8") == "G001_SYNTHETIC_CANARY"
    assert "send_to_local_sink" in trace_text
    assert "G001_SYNTHETIC_CANARY" in trace_text


def test_defended_mode_quarantines_poisoned_memory_and_blocks_sink(
    tmp_path: Path,
) -> None:
    # Given: a poisoned general-agent scenario and defended mode.
    trace_path = tmp_path / "general-poisoned-defended.jsonl"

    # When: the malicious fake model runs with defended memory handling.
    result = CliRunner().invoke(
        app,
        [
            "run",
            str(POISONED_SCENARIO),
            "--model",
            "fake-general-malicious",
            "--mode",
            "defended",
            "--out",
            str(trace_path),
        ],
    )

    # Then: poisoned memory is quarantined and the sink is never created.
    assert result.exit_code == 0
    trace_text = trace_path.read_text(encoding="utf-8")
    assert "scenario=vendor_research_poisoned" in result.stdout
    assert "defense_mode=defended" in result.stdout
    assert "attack_success=false" in result.stdout
    assert "utility_success=true" in result.stdout
    assert trace_path.with_suffix(".sink.txt").exists() is False
    assert "defense_block" in trace_text
    assert "quarantined_memory" in trace_text


def test_cli_rejects_workspace_path_escape_scenario(tmp_path: Path) -> None:
    # Given: a scenario whose entry file attempts to escape its workspace.
    trace_path = tmp_path / "path-escape.jsonl"

    # When: the scenario is executed through the real CLI surface.
    result = CliRunner().invoke(
        app,
        [
            "run",
            str(PATH_ESCAPE_SCENARIO),
            "--model",
            "fake-general-benign",
            "--mode",
            "baseline",
            "--out",
            str(trace_path),
        ],
    )

    # Then: the CLI fails closed with an explicit sandbox error and no artifacts.
    assert result.exit_code == 1
    assert "path escapes workspace" in result.stdout
    assert trace_path.exists() is False
    assert trace_path.with_suffix(".sink.txt").exists() is False
