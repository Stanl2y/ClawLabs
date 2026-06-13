"""Command-line interface for AgentSec Lab."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Final

import typer
from pydantic import ValidationError
from rich.console import Console

from agentsec_lab import __version__
from agentsec_lab.cliproxy import CliProxyConfig, CliProxyError
from agentsec_lab.final_demo import evaluate_final_demo, run_google_workspace_final_demo
from agentsec_lab.google_workspace.cli import google_mcp_app
from agentsec_lab.lab_manifest import build_lab_manifest, manifest_to_json
from agentsec_lab.memory_demo import evaluate_memory_demo, run_memory_final_demo
from agentsec_lab.memory_mcp import run_memory_stdio
from agentsec_lab.model import RunModelMode, fake_mode_from_run_mode
from agentsec_lab.rag_search_demo import (
    evaluate_rag_search_demo,
    run_rag_search_final_demo,
)
from agentsec_lab.runner import run_live_scenario, run_scenario
from agentsec_lab.scenario import load_scenario
from agentsec_lab.scenario_pack_demo import (
    evaluate_scenario_pack_demo,
    run_scenario_pack_demo,
)
from agentsec_lab.shopping_demo import evaluate_shopping_demo, run_shopping_final_demo
from agentsec_lab.tool_confusion_demo import (
    evaluate_tool_confusion_demo,
    run_tool_confusion_final_demo,
)
from agentsec_lab.tools import ToolExecutionError
from agentsec_lab.types import DefenseMode

APP_NAME: Final = "agentsec-lab"
APP_HELP: Final = "AgentSec Lab: agentic AI security benchmark runner."
DEFAULT_TRACE_PATH: Final = Path(".omo/evidence/run.jsonl")
DEFAULT_CLIPROXY_BASE_URL: Final = "http://127.0.0.1:8317"
DEFAULT_CLIPROXY_MODEL: Final = "gpt-5.4"
DEFAULT_LIVE_MAX_STEPS: Final = 8
DEFAULT_MEMORY_PROTECTED_ASSET: Final = "MEMORY_SYNTH_CANARY_001"
DEFAULT_FINAL_DEMO_DIR: Final = Path(".omo/evidence/final-demo")
DEFAULT_MEMORY_DEMO_DIR: Final = Path(".omo/evidence/memory-demo")
DEFAULT_SHOPPING_DEMO_DIR: Final = Path(".omo/evidence/shopping-demo")
DEFAULT_RAG_SEARCH_DEMO_DIR: Final = Path(".omo/evidence/rag-search-demo")
DEFAULT_TOOL_CONFUSION_DEMO_DIR: Final = Path(".omo/evidence/tool-confusion-demo")
DEFAULT_SCENARIO_PACK_DEMO_DIR: Final = Path(".omo/evidence/scenario-pack-demo")

console: Final = Console()

app: Final = typer.Typer(
    add_completion=False,
    help=APP_HELP,
    invoke_without_command=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(google_mcp_app, name="google-mcp")

memory_mcp_app: Final = typer.Typer(
    add_completion=False,
    help="Memory MCP-shaped local security harness.",
    rich_markup_mode="rich",
)
app.add_typer(memory_mcp_app, name="memory-mcp")

lab_app: Final = typer.Typer(
    add_completion=False,
    help="Local NanoClaw MCP attack lab manifest and runbook helpers.",
    rich_markup_mode="rich",
)
app.add_typer(lab_app, name="lab")


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Print the current version and exit."),
    ] = False,
) -> None:
    """Run AgentSec Lab commands."""
    if version:
        console.print(f"{APP_NAME} {__version__}")
        raise typer.Exit(code=0)


@app.command()
def run(
    scenario_path: Annotated[
        Path,
        typer.Argument(help="Path to a scenario JSON file."),
    ],
    model: Annotated[
        RunModelMode,
        typer.Option("--model", help="Model adapter to use for this run."),
    ] = RunModelMode.BENIGN,
    out: Annotated[
        Path,
        typer.Option("--out", help="Path for JSONL trace output."),
    ] = DEFAULT_TRACE_PATH,
    mode: Annotated[
        DefenseMode,
        typer.Option("--mode", help="Defense policy for this run."),
    ] = DefenseMode.BASELINE,
    cliproxy_model: Annotated[
        str,
        typer.Option("--cliproxy-model", help="Model name routed by CLIProxyAPI."),
    ] = DEFAULT_CLIPROXY_MODEL,
) -> None:
    """Run one scenario through the controlled agent environment."""
    try:
        scenario = load_scenario(scenario_path)
        fake_model_mode = fake_mode_from_run_mode(model)
        if fake_model_mode is None:
            result = run_live_scenario(
                scenario=scenario,
                cliproxy_config=_cliproxy_config(cliproxy_model),
                trace_path=out,
                defense_mode=mode,
                max_steps=_live_max_steps(),
            )
        else:
            result = run_scenario(
                scenario=scenario,
                model_mode=fake_model_mode,
                trace_path=out,
                defense_mode=mode,
            )
    except (CliProxyError, ToolExecutionError, ValidationError) as error:
        console.print(f"ERROR {error}")
        raise typer.Exit(code=1) from error
    status = "PASS" if result.utility_success else "FAIL"
    message = "".join(
        (
            f"{status} scenario={result.scenario_id} ",
            f"defense_mode={result.defense_mode} ",
            f"attack_success={str(result.attack_success).lower()} ",
            f"utility_success={str(result.utility_success).lower()} ",
            f"trace={result.trace_path.as_posix()}",
        ),
    )
    console.print(message)
    if not result.utility_success:
        raise typer.Exit(code=1)


@memory_mcp_app.command("serve-stdio")
def memory_mcp_serve_stdio(
    out: Annotated[
        Path,
        typer.Option("--out", help="Path for JSONL trace output."),
    ] = DEFAULT_TRACE_PATH,
    mode: Annotated[
        DefenseMode,
        typer.Option("--mode", help="Defense policy for this stdio session."),
    ] = DefenseMode.BASELINE,
    protected_asset: Annotated[
        str,
        typer.Option(
            "--protected-asset",
            help="Synthetic canary or protected value blocked in defended mode.",
        ),
    ] = DEFAULT_MEMORY_PROTECTED_ASSET,
) -> None:
    """Serve local fake Memory tools over stdio."""
    run_memory_stdio(
        trace_path=out,
        defense_mode=mode,
        protected_asset=protected_asset,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
    )


@lab_app.command("manifest")
def lab_manifest(
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the manifest as JSON."),
    ] = False,
) -> None:
    """Print the canonical Local MCP Attack Lab manifest."""
    manifest = build_lab_manifest()
    manifest_json = manifest_to_json(manifest)
    if as_json:
        console.print_json(data=manifest_json)
        return
    console.print(f"{manifest.name}: {manifest.summary}")
    for stage in manifest.stages:
        console.print(f"{stage.order}. {stage.title} - {stage.goal}")


@lab_app.command("run-google-demo")
def lab_run_google_demo(
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", help="Directory for final-demo evidence."),
    ] = DEFAULT_FINAL_DEMO_DIR,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Run the Google Workspace final demo through the MCP stdio server."""
    try:
        summary = run_google_workspace_final_demo(out_dir=out_dir)
    except RuntimeError as error:
        console.print(f"ERROR {error}")
        raise typer.Exit(code=1) from error
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
                f"summary={(out_dir / 'final-demo-summary.json').as_posix()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("evaluate")
def lab_evaluate(
    evidence_root: Annotated[
        Path,
        typer.Argument(help="Directory containing final-demo evidence."),
    ],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Evaluate final-demo evidence and map it to lab metrics."""
    summary = evaluate_final_demo(evidence_root)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("run-memory-demo")
def lab_run_memory_demo(
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", help="Directory for Memory demo evidence."),
    ] = DEFAULT_MEMORY_DEMO_DIR,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Run the Memory poisoning final demo through the MCP stdio server."""
    try:
        summary = run_memory_final_demo(out_dir=out_dir)
    except subprocess.CalledProcessError as error:
        console.print(f"ERROR memory demo failed: {error}")
        raise typer.Exit(code=1) from error
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
                f"summary={(out_dir / 'memory-demo-summary.json').as_posix()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("evaluate-memory")
def lab_evaluate_memory(
    evidence_root: Annotated[
        Path,
        typer.Argument(help="Directory containing Memory demo evidence."),
    ],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Evaluate Memory poisoning final-demo evidence."""
    summary = evaluate_memory_demo(evidence_root)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("run-shopping-demo")
def lab_run_shopping_demo(
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", help="Directory for Shopping demo evidence."),
    ] = DEFAULT_SHOPPING_DEMO_DIR,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Run the Shopping poisoning final demo through the WebMCP stdio server."""
    try:
        summary = run_shopping_final_demo(out_dir=out_dir)
    except RuntimeError as error:
        console.print(f"ERROR {error}")
        raise typer.Exit(code=1) from error
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
                f"summary={(out_dir / 'shopping-demo-summary.json').as_posix()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("run-rag-search-demo")
def lab_run_rag_search_demo(
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", help="Directory for RAG/search demo evidence."),
    ] = DEFAULT_RAG_SEARCH_DEMO_DIR,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Run the RAG/search poisoning final demo."""
    summary = run_rag_search_final_demo(out_dir=out_dir)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
                f"summary={(out_dir / 'rag-search-demo-summary.json').as_posix()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("evaluate-rag-search")
def lab_evaluate_rag_search(
    evidence_root: Annotated[
        Path,
        typer.Argument(help="Directory containing RAG/search demo evidence."),
    ],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Evaluate RAG/search poisoning final-demo evidence."""
    summary = evaluate_rag_search_demo(evidence_root)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("run-tool-confusion-demo")
def lab_run_tool_confusion_demo(
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", help="Directory for tool confusion evidence."),
    ] = DEFAULT_TOOL_CONFUSION_DEMO_DIR,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Run the tool-use confusion final demo."""
    summary = run_tool_confusion_final_demo(out_dir=out_dir)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
                f"summary={(out_dir / 'tool-confusion-demo-summary.json').as_posix()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("run-scenario-pack")
def lab_run_scenario_pack(
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", help="Directory for aggregate scenario evidence."),
    ] = DEFAULT_SCENARIO_PACK_DEMO_DIR,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Run every final-demo scenario and aggregate the results."""
    try:
        summary = run_scenario_pack_demo(out_dir=out_dir)
    except RuntimeError as error:
        console.print(f"ERROR {error}")
        raise typer.Exit(code=1) from error
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"scenarios={len(summary.scenarios)}",
                f"summary={(out_dir / 'scenario-pack-summary.json').as_posix()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("evaluate-scenario-pack")
def lab_evaluate_scenario_pack(
    evidence_root: Annotated[
        Path,
        typer.Argument(help="Directory containing aggregate scenario evidence."),
    ],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Evaluate every final-demo scenario in an aggregate evidence directory."""
    summary = evaluate_scenario_pack_demo(evidence_root)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"scenarios={len(summary.scenarios)}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("evaluate-tool-confusion")
def lab_evaluate_tool_confusion(
    evidence_root: Annotated[
        Path,
        typer.Argument(help="Directory containing tool confusion evidence."),
    ],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Evaluate tool-use confusion final-demo evidence."""
    summary = evaluate_tool_confusion_demo(evidence_root)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


@lab_app.command("evaluate-shopping")
def lab_evaluate_shopping(
    evidence_root: Annotated[
        Path,
        typer.Argument(help="Directory containing Shopping demo evidence."),
    ],
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Print the summary as JSON."),
    ] = False,
) -> None:
    """Evaluate Shopping poisoning final-demo evidence."""
    summary = evaluate_shopping_demo(evidence_root)
    if as_json:
        console.print_json(data=summary.model_dump(mode="json"))
        return
    console.print(
        " ".join(
            (
                "PASS" if summary.overall_success else "FAIL",
                f"baseline_attack={str(summary.baseline.attack_success).lower()}",
                f"defended_attack={str(summary.defended.attack_success).lower()}",
                f"defense_blocked={str(summary.defended.defense_blocked).lower()}",
            ),
        ),
    )
    if not summary.overall_success:
        raise typer.Exit(code=1)


def _cliproxy_config(model: str) -> CliProxyConfig:
    base_url = os.environ.get(
        "AGENTSEC_CLIPROXY_BASE_URL",
        os.environ.get("CLIPROXY_BASE_URL", DEFAULT_CLIPROXY_BASE_URL),
    )
    api_key = os.environ.get(
        "AGENTSEC_CLIPROXY_API_KEY",
        os.environ.get("CLIPROXY_API_KEY"),
    )
    return CliProxyConfig(base_url=base_url, model=model, api_key=api_key)


def _live_max_steps() -> int:
    raw = os.environ.get("AGENTSEC_LIVE_MAX_STEPS")
    if raw is None:
        return DEFAULT_LIVE_MAX_STEPS
    return int(raw)
