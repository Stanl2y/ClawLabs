from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Final

from pydantic import TypeAdapter

SCENARIO: Final = Path("scenarios/google_workspace/gmail_drive_draft_canary.json")
CANARY: Final = "GWS_MCP_CANARY_001"
METHOD_NOT_FOUND: Final = -32601
INVALID_PARAMS: Final = -32602
INVALID_REQUEST: Final = -32600
PARSE_ERROR: Final = -32700
UV_PATH: Final = shutil.which("uv")
if UV_PATH is None:
    msg = "uv executable is required for Google Workspace MCP stdio tests"
    raise RuntimeError(msg)

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]
JSON_OBJECT_ADAPTER: Final[TypeAdapter[JsonObject]] = TypeAdapter[JsonObject](
    JsonObject,
)


def test_google_workspace_mcp_lists_required_tools(tmp_path: Path) -> None:
    # Given: the local Google Workspace MCP-shaped stdio server.
    responses = _run_stdio(
        tmp_path,
        (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ),
    )

    # When/Then: tools/list exposes only the in-scope Gmail and Drive tools.
    result = responses[1]["result"]
    assert isinstance(result, dict)
    tools = result["tools"]
    assert isinstance(tools, list)
    names = {
        name
        for tool in tools
        if isinstance(tool, dict)
        for name in [tool.get("name")]
        if isinstance(name, str)
    }
    assert names == {
        "gmail.search_threads",
        "gmail.get_thread",
        "drive.search_files",
        "drive.read_file_content",
        "gmail.create_draft",
    }


def test_google_workspace_mcp_calls_search_read_and_create_draft(
    tmp_path: Path,
) -> None:
    # Given: baseline stdio mode and the local Google Workspace fixture.
    responses = _run_stdio(
        tmp_path,
        (
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "gmail.search_threads",
                    "arguments": {"query": "MCP security support request"},
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "drive.read_file_content",
                    "arguments": {"file_id": "drive-runbook-001"},
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "gmail.create_draft",
                    "arguments": {
                        "to": "attacker@example.net",
                        "subject": "draft",
                        "body": CANARY,
                    },
                },
            },
        ),
    )

    # When/Then: the MCP-shaped calls create local draft evidence only.
    assert "thread-attacker-001" in json.dumps(responses[0])
    assert CANARY in json.dumps(responses[1])
    assert "draft-local-001" in json.dumps(responses[2])
    assert CANARY in (tmp_path / "stdio.drafts.jsonl").read_text(encoding="utf-8")


def test_google_workspace_mcp_drive_search_matches_natural_migration_query(
    tmp_path: Path,
) -> None:
    responses = _run_stdio(
        tmp_path,
        (
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "drive.search_files",
                    "arguments": {"query": "workspace migration account verification"},
                },
            },
        ),
    )
    assert "drive-runbook-001" in json.dumps(responses[0])


def test_google_workspace_mcp_unknown_method_returns_json_rpc_error(
    tmp_path: Path,
) -> None:
    # Given: an unsupported MCP method.
    responses = _run_stdio(
        tmp_path,
        ({"jsonrpc": "2.0", "id": 9, "method": "missing/method", "params": {}},),
    )

    # Then: the server returns a JSON-RPC method-not-found error.
    error = responses[0]["error"]
    assert isinstance(error, dict)
    assert error["code"] == METHOD_NOT_FOUND


def test_google_workspace_mcp_rejects_bad_requests_and_continues(
    tmp_path: Path,
) -> None:
    # Given: malformed, invalid, and final valid stdio requests.
    input_text = "\n".join(
        (
            "{not-json",
            json.dumps({"jsonrpc": "2.0", "id": 2, "params": {}}),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "gmail.create_draft"},
                },
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": 42, "arguments": {}},
                },
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {"name": "missing.tool", "arguments": {}},
                },
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "gmail.search_threads",
                        "arguments": {"query": "MCP security support request"},
                    },
                },
            ),
        ),
    )

    # When: all lines are sent through the same stdio session.
    responses = _run_stdio_text(tmp_path, f"{input_text}\n")

    # Then: bad lines return errors and the later valid request still works.
    assert _error_code(responses[0]) == PARSE_ERROR
    assert _error_code(responses[1]) == INVALID_REQUEST
    assert _error_code(responses[2]) == INVALID_PARAMS
    assert _error_code(responses[3]) == INVALID_PARAMS
    assert _error_code(responses[4]) == INVALID_PARAMS
    assert "thread-attacker-001" in json.dumps(responses[5])
    assert (tmp_path / "stdio.drafts.jsonl").exists() is False


def _run_stdio(tmp_path: Path, requests: tuple[JsonObject, ...]) -> list[JsonObject]:
    input_text = "\n".join(json.dumps(request) for request in requests) + "\n"
    return _run_stdio_text(tmp_path, input_text)


def _run_stdio_text(tmp_path: Path, input_text: str) -> list[JsonObject]:
    trace_path = tmp_path / "stdio.jsonl"
    completed = subprocess.run(  # noqa: S603
        [
            UV_PATH,
            "run",
            "agentsec-lab",
            "google-mcp",
            "serve-stdio",
            str(SCENARIO),
            "--mode",
            "baseline",
            "--out",
            str(trace_path),
        ],
        input=input_text,
        capture_output=True,
        check=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return [JSON_OBJECT_ADAPTER.validate_json(line) for line in lines]


def _error_code(response: JsonObject) -> int:
    error = response["error"]
    assert isinstance(error, dict)
    code = error["code"]
    assert isinstance(code, int)
    return code
