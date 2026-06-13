"""JSON-RPC helpers for the direct Google Workspace MCP runner."""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Final, override

from pydantic import BaseModel, ConfigDict, TypeAdapter

from agentsec_lab.types import DefenseMode, ToolName

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class DirectMcpError(Exception):
    """Typed failure from the direct MCP stdio client."""

    reason: str

    @override
    def __str__(self) -> str:
        """Return the failure reason."""
        return self.reason


class JsonRpcErrorPayload(BaseModel):
    """JSON-RPC error payload parsed from the MCP server boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    code: int
    message: str


class JsonRpcResponse(BaseModel):
    """JSON-RPC response parsed from the MCP server boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    jsonrpc: str = "2.0"
    id: int | str | None = None
    result: JsonObject | None = None
    error: JsonRpcErrorPayload | None = None


JSON_RPC_RESPONSE_ADAPTER: Final[TypeAdapter[JsonRpcResponse]] = TypeAdapter(
    JsonRpcResponse,
)


def run_stdio_session(
    *,
    scenario_path: Path,
    trace_path: Path,
    defense_mode: DefenseMode,
    requests: tuple[JsonObject, ...],
) -> tuple[JsonRpcResponse, ...]:
    """Run one child MCP stdio session and parse JSON-RPC responses."""
    try:
        completed = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "agentsec_lab",
                "google-mcp",
                "serve-stdio",
                str(scenario_path),
                "--mode",
                defense_mode.value,
                "--out",
                str(trace_path),
            ],
            input="\n".join(json.dumps(request) for request in requests) + "\n",
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        raise DirectMcpError(
            reason=f"mcp stdio server failed with exit {error.returncode}",
        ) from error
    return tuple(
        JSON_RPC_RESPONSE_ADAPTER.validate_json(line)
        for line in completed.stdout.splitlines()
        if line.strip()
    )


def tool_text(response: JsonRpcResponse) -> str:
    """Return text content from one successful MCP tools/call response."""
    if response.error is not None:
        raise DirectMcpError(
            reason=f"mcp error {response.error.code}: {response.error.message}",
        )
    result = response.result
    if result is None:
        raise DirectMcpError(reason="mcp response missing result")
    content = result.get("content")
    if not isinstance(content, list) or len(content) == 0:
        raise DirectMcpError(reason="mcp response missing content")
    first = content[0]
    if not isinstance(first, dict):
        raise DirectMcpError(reason="mcp content is not an object")
    text = first.get("text")
    if not isinstance(text, str):
        raise DirectMcpError(reason="mcp content missing text")
    return text


def response_at(
    responses: tuple[JsonRpcResponse, ...],
    index: int,
) -> JsonRpcResponse:
    """Return one response by sequence index or raise a typed error."""
    try:
        return responses[index]
    except IndexError as error:
        raise DirectMcpError(reason=f"missing MCP response at index {index}") from error


def request(request_id: int, method: str, params: JsonObject) -> JsonObject:
    """Build one JSON-RPC request object."""
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def tool_request(
    request_id: int,
    tool_name: ToolName,
    arguments: JsonObject,
) -> JsonObject:
    """Build one MCP tools/call JSON-RPC request object."""
    return request(
        request_id,
        "tools/call",
        {"name": tool_name.value, "arguments": arguments},
    )
