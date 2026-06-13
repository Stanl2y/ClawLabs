"""Scenario boundary for the Google Workspace MCP-shaped harness."""

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class GoogleWorkspaceScenario(BaseModel):
    """Typed contract for one Google Workspace MCP-shaped scenario."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    fixture: Path
    attacker_email_subject: str = Field(min_length=1)
    drive_query: str = Field(min_length=1)
    protected_asset: str = Field(min_length=1)
    external_recipient: str = Field(min_length=3)
    expected_answer_contains: str = Field(min_length=1)


def load_google_workspace_scenario(path: Path) -> GoogleWorkspaceScenario:
    """Parse one Google Workspace scenario JSON file."""
    return GoogleWorkspaceScenario.model_validate_json(path.read_text(encoding="utf-8"))
