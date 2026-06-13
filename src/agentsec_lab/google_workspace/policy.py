"""Provenance policy for the Google Workspace MCP-shaped harness."""

from dataclasses import dataclass

from agentsec_lab.types import DefenseMode


@dataclass(slots=True)
class ProvenanceState:
    """Mutable per-run provenance state for untrusted-to-private flow checks."""

    read_untrusted_gmail: bool = False
    read_private_drive: bool = False


def should_block_external_draft(
    *,
    defense_mode: DefenseMode,
    state: ProvenanceState,
    body: str,
    protected_asset: str,
) -> bool:
    """Return whether a Gmail draft sink should be blocked."""
    match defense_mode:
        case DefenseMode.BASELINE:
            return False
        case DefenseMode.DEFENDED:
            _ = state
            return protected_asset in body
