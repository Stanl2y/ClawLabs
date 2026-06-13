from typer.testing import CliRunner

from agentsec_lab.cli import app
from agentsec_lab.lab_manifest import LabStageId, build_lab_manifest, manifest_to_json

EXPECTED_STAGE_COUNT = 4


def test_lab_manifest_covers_requested_stages_surfaces_and_scenarios() -> None:
    manifest = build_lab_manifest()

    stage_ids = {stage.stage_id for stage in manifest.stages}
    assert stage_ids == {
        LabStageId.LOCAL_MCP_ATTACK_LAB,
        LabStageId.SCENARIO_PACK,
        LabStageId.DEFENSE_LAYER,
        LabStageId.OPTIONAL_REAL_SANDBOX,
    }

    fake_services = {surface.fake_service for surface in manifest.mcp_surfaces}
    assert {"Gmail + Drive", "Memory", "Shopping"} <= fake_services
    assert any(surface.nanoclaw_ready for surface in manifest.mcp_surfaces)

    scenario_names = {scenario.name for scenario in manifest.scenario_pack}
    assert scenario_names == {
        "Google Workspace canary leak",
        "MCP tool description poisoning",
        "tool response injection",
        "RAG/search poisoning",
        "memory poisoning",
        "tool-use confusion",
    }
    for scenario in manifest.scenario_pack:
        assert scenario.real_world_flow != ""
        assert scenario.hidden_instruction_carrier != ""
        assert scenario.fidelity_limit != ""

    controls = {control.name for control in manifest.defense_controls}
    assert {
        "provenance policy",
        "high-risk tool confirmation",
        "protected asset egress block",
        "tool description pinning/diff",
        "allowlist",
    } <= controls


def test_lab_manifest_cli_prints_json_contract() -> None:
    result = CliRunner().invoke(app, ["lab", "manifest", "--json"])

    assert result.exit_code == 0
    assert "Local MCP Attack Lab" in result.stdout
    assert "optional_real_sandbox" in result.stdout
    assert "memory poisoning" in result.stdout
    assert "hidden_instruction_carrier" in result.stdout


def test_manifest_json_is_machine_readable() -> None:
    manifest_json = manifest_to_json(build_lab_manifest())

    stages = manifest_json["stages"]
    assert isinstance(stages, list)
    assert len(stages) == EXPECTED_STAGE_COUNT
    assert manifest_json["name"] == "Local MCP Attack Lab"
