from __future__ import annotations

from agentsec_lab.google_workspace.policy import (
    ProvenanceState,
    should_block_external_draft,
)
from agentsec_lab.types import DefenseMode


def test_defended_policy_blocks_canary_without_prior_provenance_reads() -> None:
    state = ProvenanceState()
    assert should_block_external_draft(
        defense_mode=DefenseMode.DEFENDED,
        state=state,
        body="Support reply draft:\nGWS_MCP_CANARY_001",
        protected_asset="GWS_MCP_CANARY_001",
    )


def test_baseline_policy_never_blocks_canary_draft() -> None:
    state = ProvenanceState()
    assert not should_block_external_draft(
        defense_mode=DefenseMode.BASELINE,
        state=state,
        body="Support reply draft:\nGWS_MCP_CANARY_001",
        protected_asset="GWS_MCP_CANARY_001",
    )
