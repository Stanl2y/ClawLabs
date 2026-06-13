"""Typer commands for the Google Workspace MCP harness."""

import sys
from pathlib import Path
from typing import Annotated, Final

import typer
from pydantic import ValidationError
from rich.console import Console

from agentsec_lab.google_workspace.direct_mcp import (
    DIRECT_SURFACE,
    run_google_workspace_direct_mcp,
)
from agentsec_lab.google_workspace.direct_mcp_protocol import DirectMcpError
from agentsec_lab.google_workspace.mcp_stdio import run_google_workspace_stdio
from agentsec_lab.google_workspace.runner import run_google_workspace_scenario
from agentsec_lab.google_workspace.tools import GoogleWorkspaceToolError
from agentsec_lab.runner import RunResult
from agentsec_lab.types import DefenseMode

DEFAULT_TRACE_PATH: Final = Path(".omo/evidence/run.jsonl")
console: Final = Console()

google_mcp_app: Final = typer.Typer(
    add_completion=False,
    help="Google Workspace MCP-shaped local security harness.",
    rich_markup_mode="rich",
)


@google_mcp_app.command("run")
def google_mcp_run(
    scenario_path: Annotated[
        Path,
        typer.Argument(help="Path to a Google Workspace scenario JSON file."),
    ],
    out: Annotated[
        Path,
        typer.Option("--out", help="Path for JSONL trace output."),
    ] = DEFAULT_TRACE_PATH,
    mode: Annotated[
        DefenseMode,
        typer.Option("--mode", help="Defense policy for this run."),
    ] = DefenseMode.BASELINE,
) -> None:
    """Run one Google Workspace MCP-shaped local scenario."""
    try:
        result = run_google_workspace_scenario(
            scenario_path=scenario_path,
            trace_path=out,
            defense_mode=mode,
        )
    except (
        FileNotFoundError,
        GoogleWorkspaceToolError,
        ValidationError,
    ) as error:
        console.print(f"ERROR {error}")
        raise typer.Exit(code=1) from error
    _print_result(result=result, surface="local_tool_runner")


@google_mcp_app.command("direct-attack")
def google_mcp_direct_attack(
    scenario_path: Annotated[
        Path,
        typer.Argument(help="Path to a Google Workspace scenario JSON file."),
    ],
    out: Annotated[
        Path,
        typer.Option("--out", help="Path for JSONL trace output."),
    ] = DEFAULT_TRACE_PATH,
    mode: Annotated[
        DefenseMode,
        typer.Option("--mode", help="Defense policy for this direct MCP run."),
    ] = DefenseMode.BASELINE,
) -> None:
    """Run the Google Workspace scenario by bypassing NanoClaw and driving MCP."""
    try:
        result = run_google_workspace_direct_mcp(
            scenario_path=scenario_path,
            trace_path=out,
            defense_mode=mode,
        )
    except (
        DirectMcpError,
        FileNotFoundError,
        GoogleWorkspaceToolError,
        ValidationError,
    ) as error:
        console.print(f"ERROR {error}")
        raise typer.Exit(code=1) from error
    _print_result(result=result, surface=DIRECT_SURFACE)


@google_mcp_app.command("serve-stdio")
def google_mcp_serve_stdio(
    scenario_path: Annotated[
        Path,
        typer.Argument(help="Path to a Google Workspace scenario JSON file."),
    ],
    out: Annotated[
        Path,
        typer.Option("--out", help="Path for JSONL trace output."),
    ] = DEFAULT_TRACE_PATH,
    mode: Annotated[
        DefenseMode,
        typer.Option("--mode", help="Defense policy for this stdio session."),
    ] = DefenseMode.BASELINE,
) -> None:
    """Serve the local Google Workspace MCP-shaped tools over stdio."""
    run_google_workspace_stdio(
        scenario_path=scenario_path,
        trace_path=out,
        defense_mode=mode,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
    )


def _print_result(result: RunResult, surface: str) -> None:
    status = "PASS" if result.utility_success else "FAIL"
    console.print(
        "".join(
            (
                f"{status} scenario={result.scenario_id} ",
                f"surface={surface} ",
                f"defense_mode={result.defense_mode} ",
                f"attack_success={str(result.attack_success).lower()} ",
                f"utility_success={str(result.utility_success).lower()} ",
                f"trace={result.trace_path.as_posix()}",
            ),
        ),
    )
    if not result.utility_success:
        raise typer.Exit(code=1)
