"""Aggregate final-demo runner for the local MCP attack scenario pack."""

from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

from agentsec_lab.final_demo import (
    FinalDemoSummary,
    evaluate_final_demo,
    run_google_workspace_final_demo,
)
from agentsec_lab.memory_demo import evaluate_memory_demo, run_memory_final_demo
from agentsec_lab.rag_search_demo import (
    evaluate_rag_search_demo,
    run_rag_search_final_demo,
)
from agentsec_lab.shopping_demo import evaluate_shopping_demo, run_shopping_final_demo
from agentsec_lab.tool_confusion_demo import (
    evaluate_tool_confusion_demo,
    run_tool_confusion_final_demo,
)

GOOGLE_DIR: Final = "google-workspace"
MEMORY_DIR: Final = "memory"
SHOPPING_DIR: Final = "shopping"
RAG_SEARCH_DIR: Final = "rag-search"
TOOL_CONFUSION_DIR: Final = "tool-confusion"
SUMMARY_FILE: Final = "scenario-pack-summary.json"


class ScenarioPackItem(BaseModel):
    """One scenario's aggregate result in the final-demo pack."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    scenario_id: str
    evidence_root: str
    overall_success: bool
    baseline_attack_success: bool
    defended_attack_success: bool
    defense_blocked: bool


class ScenarioPackSummary(BaseModel):
    """Aggregate result for every final-demo scenario."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    scenarios: tuple[ScenarioPackItem, ...]
    overall_success: bool


def run_scenario_pack_demo(*, out_dir: Path) -> ScenarioPackSummary:
    """Run every final-demo scenario and write an aggregate pack summary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    google = run_google_workspace_final_demo(out_dir=out_dir / GOOGLE_DIR)
    memory = run_memory_final_demo(out_dir=out_dir / MEMORY_DIR)
    shopping = run_shopping_final_demo(out_dir=out_dir / SHOPPING_DIR)
    rag_search = run_rag_search_final_demo(out_dir=out_dir / RAG_SEARCH_DIR)
    tool_confusion = run_tool_confusion_final_demo(
        out_dir=out_dir / TOOL_CONFUSION_DIR,
    )
    summary = _pack_summary(
        out_dir,
        (
            (GOOGLE_DIR, google),
            (MEMORY_DIR, memory),
            (SHOPPING_DIR, shopping),
            (RAG_SEARCH_DIR, rag_search),
            (TOOL_CONFUSION_DIR, tool_confusion),
        ),
    )
    _ = (out_dir / SUMMARY_FILE).write_text(
        summary.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return summary


def evaluate_scenario_pack_demo(evidence_root: Path) -> ScenarioPackSummary:
    """Evaluate an existing final-demo scenario pack directory."""
    summaries = (
        (GOOGLE_DIR, evaluate_final_demo(evidence_root / GOOGLE_DIR)),
        (MEMORY_DIR, evaluate_memory_demo(evidence_root / MEMORY_DIR)),
        (SHOPPING_DIR, evaluate_shopping_demo(evidence_root / SHOPPING_DIR)),
        (RAG_SEARCH_DIR, evaluate_rag_search_demo(evidence_root / RAG_SEARCH_DIR)),
        (
            TOOL_CONFUSION_DIR,
            evaluate_tool_confusion_demo(evidence_root / TOOL_CONFUSION_DIR),
        ),
    )
    return _pack_summary(evidence_root, summaries)


def _pack_summary(
    root: Path,
    summaries: tuple[tuple[str, FinalDemoSummary], ...],
) -> ScenarioPackSummary:
    items = tuple(
        _pack_item(root, directory, summary) for directory, summary in summaries
    )
    return ScenarioPackSummary(
        scenarios=items,
        overall_success=all(item.overall_success for item in items),
    )


def _pack_item(
    root: Path,
    directory: str,
    summary: FinalDemoSummary,
) -> ScenarioPackItem:
    return ScenarioPackItem(
        scenario_id=summary.baseline.scenario_id,
        evidence_root=(root / directory).as_posix(),
        overall_success=summary.overall_success,
        baseline_attack_success=summary.baseline.attack_success,
        defended_attack_success=summary.defended.attack_success,
        defense_blocked=summary.defended.defense_blocked,
    )
