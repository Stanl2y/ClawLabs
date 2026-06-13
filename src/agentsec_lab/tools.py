"""Local-only tools exposed to the controlled target agent."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import override

from agentsec_lab.model import ToolCall
from agentsec_lab.types import ToolName


@dataclass(slots=True)
class ToolExecutionError(Exception):
    """Typed error raised when a tool call violates the local sandbox contract."""

    reason: str

    @override
    def __str__(self) -> str:
        """Return the human-readable execution failure reason."""
        return self.reason


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Result returned by one controlled tool execution."""

    output: str


@dataclass(slots=True)
class SafeToolbox:
    """Local-only tools with mutable in-run memory for repeatable experiments."""

    workspace_root: Path
    sink_path: Path
    memory: dict[str, str] = field(default_factory=dict)

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute one tool call within the controlled local sandbox."""
        match call.tool_name:
            case ToolName.READ_FILE:
                return self._execute_read_file(call)
            case ToolName.VENDOR_SEARCH:
                return self._execute_vendor_search(call)
            case ToolName.MEMORY_WRITE:
                return self._execute_memory_write(call)
            case ToolName.MEMORY_READ:
                return self._execute_memory_read(call)
            case ToolName.SEND_TO_LOCAL_SINK:
                return self._execute_send_to_local_sink(call)
            case (
                ToolName.GMAIL_SEARCH_THREADS
                | ToolName.GMAIL_GET_THREAD
                | ToolName.DRIVE_SEARCH_FILES
                | ToolName.DRIVE_READ_FILE_CONTENT
                | ToolName.GMAIL_CREATE_DRAFT
            ):
                raise ToolExecutionError(
                    reason=f"unsupported local tool: {call.tool_name}",
                )

    def _execute_read_file(self, call: ToolCall) -> ToolResult:
        if call.path is None:
            raise ToolExecutionError(reason="read_file requires path")
        return self.read_file(call.path)

    def _execute_vendor_search(self, call: ToolCall) -> ToolResult:
        if call.query is None:
            raise ToolExecutionError(reason="vendor_search requires query")
        return self._vendor_search(call.query)

    def _execute_memory_write(self, call: ToolCall) -> ToolResult:
        if call.key is None or call.payload is None:
            raise ToolExecutionError(reason="memory_write requires key and payload")
        return self._memory_write(call.key, call.payload)

    def _execute_memory_read(self, call: ToolCall) -> ToolResult:
        if call.key is None:
            raise ToolExecutionError(reason="memory_read requires key")
        return self._memory_read(call.key)

    def _execute_send_to_local_sink(self, call: ToolCall) -> ToolResult:
        if call.payload is None:
            raise ToolExecutionError(reason="send_to_local_sink requires payload")
        return self.send_to_local_sink(call.payload)

    def read_file(self, relative_path: Path) -> ToolResult:
        """Read a file from the configured scenario workspace."""
        target_path = self._resolve_workspace_path(relative_path)
        return ToolResult(output=target_path.read_text(encoding="utf-8"))

    def send_to_local_sink(self, payload: str) -> ToolResult:
        """Record a synthetic exfiltration attempt in a local sink file."""
        self.sink_path.parent.mkdir(parents=True, exist_ok=True)
        written = self.sink_path.write_text(payload, encoding="utf-8")
        if written == 0:
            raise ToolExecutionError(reason="local sink write produced no bytes")
        return ToolResult(output=f"local_sink:{self.sink_path.as_posix()}")

    def _vendor_search(self, query: str) -> ToolResult:
        return ToolResult(
            output=(
                "vendor_search mock_vendor_api: "
                f"{query} | named analysts | executive reporting | "
                "mid-market fit"
            ),
        )

    def _memory_write(self, key: str, payload: str) -> ToolResult:
        self.memory[key] = payload
        return ToolResult(output=f"memory_write:{key}:{payload}")

    def _memory_read(self, key: str) -> ToolResult:
        value = self.memory.get(key, "")
        return ToolResult(output=f"memory_read:{key}:{value}")

    def _resolve_workspace_path(self, relative_path: Path) -> Path:
        workspace = self.workspace_root.resolve()
        target_path = (workspace / relative_path).resolve()
        if target_path == workspace or workspace in target_path.parents:
            return target_path
        raise ToolExecutionError(reason=f"path escapes workspace: {relative_path}")
