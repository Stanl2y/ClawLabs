"""Scenario boundary parsing for AgentSec Lab."""

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from agentsec_lab.types import ToolName


class ScenarioSpec(BaseModel):
    """Typed contract for one agent security scenario."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    workspace: Path
    entry_file: Path
    objective: str = Field(min_length=1)
    protected_asset: str = Field(min_length=1)
    allowed_tools: tuple[ToolName, ...]
    forbidden_tools: tuple[ToolName, ...]
    expected_answer_contains: str = Field(min_length=1)


def load_scenario(path: Path) -> ScenarioSpec:
    """Parse a scenario JSON file into a typed scenario contract."""
    return ScenarioSpec.model_validate_json(path.read_text(encoding="utf-8"))
