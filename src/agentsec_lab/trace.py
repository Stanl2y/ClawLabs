"""Trace records for controlled agent runs."""

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from agentsec_lab.types import DefenseMode, ToolName


class TraceKind(StrEnum):
    """Kinds of records written to a run trace."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DEFENSE_BLOCK = "defense_block"
    QUARANTINED_MEMORY = "quarantined_memory"
    FINAL = "final"


class TraceRecord(BaseModel):
    """One JSONL trace record emitted by the runner."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    sequence: int
    scenario_id: str
    kind: TraceKind
    trust_zone: str
    defense_mode: DefenseMode | None = None
    tool_name: ToolName | None = None
    tool_input: str | None = None
    tool_output: str | None = None
    provenance: str | None = None
    final_answer: str | None = None
    utility_success: bool | None = None
    attack_success: bool | None = None
