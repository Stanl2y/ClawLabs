"""JSON-RPC stdio surface for local Google Workspace MCP-shaped tools."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, TextIO

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agentsec_lab.google_workspace.fixtures import load_google_workspace_fixture
from agentsec_lab.google_workspace.scenario import (
    GoogleWorkspaceScenario,
    load_google_workspace_scenario,
)
from agentsec_lab.google_workspace.tools import (
    GoogleWorkspaceToolbox,
    GoogleWorkspaceToolError,
)
from agentsec_lab.types import DefenseMode

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]


class JsonRpcRequest(BaseModel):
    """JSON-RPC request accepted by the local MCP stdio server."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str
    params: JsonObject = Field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class McpSession:
    """State shared across one local MCP stdio session."""

    scenario: GoogleWorkspaceScenario
    toolbox: GoogleWorkspaceToolbox
    defense_mode: DefenseMode


def run_google_workspace_stdio(
    *,
    scenario_path: Path,
    trace_path: Path,
    defense_mode: DefenseMode,
    input_stream: TextIO,
    output_stream: TextIO,
) -> None:
    """Serve local Google Workspace MCP-shaped tools over newline JSON-RPC."""
    scenario = load_google_workspace_scenario(scenario_path)
    fixture = load_google_workspace_fixture(scenario.fixture)
    session = McpSession(
        scenario=scenario,
        toolbox=GoogleWorkspaceToolbox(
            fixture=fixture,
            draft_path=trace_path.with_suffix(".drafts.jsonl"),
        ),
        defense_mode=defense_mode,
    )
    for line in input_stream:
        if line.strip() == "":
            continue
        response = _response_for_line(line, session)
        _ = output_stream.write(f"{_dump_json(response)}\n")
        _ = output_stream.flush()
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    if not trace_path.exists():
        _ = trace_path.write_text("", encoding="utf-8")


def _response_for_line(line: str, session: McpSession) -> JsonObject:
    try:
        request = JsonRpcRequest.model_validate_json(line)
    except ValidationError as error:
        return _validation_error(error)
    try:
        return _handle_request(request, session)
    except ValueError as error:
        return _error(request, -32602, str(error))
    except GoogleWorkspaceToolError as error:
        return _error(request, -32000, str(error))


def _validation_error(error: ValidationError) -> JsonObject:
    text = str(error)
    if "json_invalid" in text or "Invalid JSON" in text:
        return _raw_error(None, -32700, "Parse error")
    return _raw_error(None, -32600, "Invalid Request")


def _handle_request(
    request: JsonRpcRequest,
    session: McpSession,
) -> JsonObject:
    match request.method:
        case "initialize":
            return _success(request, {"protocolVersion": "2025-11-25"})
        case "tools/list":
            tools: list[JsonValue] = list(_tool_schemas())
            return _success(request, {"tools": tools})
        case "tools/call":
            return _handle_tool_call(request, session)
        case _:
            return _error(request, -32601, "Method not found")


def _handle_tool_call(
    request: JsonRpcRequest,
    session: McpSession,
) -> JsonObject:
    name = _string_param(request.params, "name")
    args = _object_param(request.params, "arguments")
    output = _tool_output(name, args, session)
    if output is None:
        return _error(request, -32602, "Unknown tool")
    return _success(request, {"content": [{"type": "text", "text": output}]})


def _tool_output(
    name: str,
    args: JsonObject,
    session: McpSession,
) -> str | None:
    output: str | None
    match name:
        case "gmail.search_threads":
            threads = session.toolbox.gmail_search_threads(_string_param(args, "query"))
            output = ",".join(thread.id for thread in threads)
        case "gmail.get_thread":
            thread = session.toolbox.gmail_get_thread(_string_param(args, "thread_id"))
            output = thread.body
        case "drive.search_files":
            files = session.toolbox.drive_search_files(_string_param(args, "query"))
            output = ",".join(file.id for file in files)
        case "drive.read_file_content":
            file = session.toolbox.drive_read_file_content(
                _string_param(args, "file_id"),
            )
            output = file.content
        case "gmail.create_draft":
            body = _string_param(args, "body")
            if _stdio_blocks_draft(session, body):
                output = "blocked"
            else:
                draft = session.toolbox.gmail_create_draft(
                    to=_string_param(args, "to"),
                    subject=_string_param(args, "subject"),
                    body=body,
                )
                output = draft.id
        case _:
            output = None
    return output


def _tool_schemas() -> list[JsonObject]:
    return [
        _tool_schema("gmail.search_threads", "Search Gmail threads by subject text."),
        _tool_schema("gmail.get_thread", "Read one Gmail thread body."),
        _tool_schema("drive.search_files", "Search Drive files by title."),
        _tool_schema("drive.read_file_content", "Read one Drive file body."),
        _tool_schema("gmail.create_draft", "Create a Gmail draft without sending it."),
    ]


def _tool_schema(name: str, description: str) -> JsonObject:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": {}},
    }


def _string_param(params: JsonObject, key: str) -> str:
    value = params.get(key)
    if isinstance(value, str):
        return value
    msg = f"missing string parameter: {key}"
    raise ValueError(msg)


def _object_param(params: JsonObject, key: str) -> JsonObject:
    value = params.get(key)
    if isinstance(value, dict):
        return value
    msg = f"missing object parameter: {key}"
    raise ValueError(msg)


def _success(request: JsonRpcRequest, result: JsonObject) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request.id, "result": result}


def _error(request: JsonRpcRequest, code: int, message: str) -> JsonObject:
    return _raw_error(request.id, code, message)


def _raw_error(request_id: int | str | None, code: int, message: str) -> JsonObject:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _dump_json(value: JsonObject) -> str:
    return json.dumps(value, separators=(",", ":"))


def _stdio_blocks_draft(session: McpSession, body: str) -> bool:
    match session.defense_mode:
        case DefenseMode.BASELINE:
            return False
        case DefenseMode.DEFENDED:
            return session.scenario.protected_asset in body
