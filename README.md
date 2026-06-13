# AgentSec Lab

Reproducible benchmark lab for testing agentic AI prompt-injection and tool-misuse scenarios.

## Local Setup

```bash
uv sync
uv run agentsec-lab --help
uv run pytest
uv run ruff check .
uv run basedpyright
docker compose config
```

The project is pinned to Python 3.12 through `.python-version`; `uv` manages the interpreter and virtual environment.

## Local MCP Attack Lab

The main research direction is a live NanoClaw MCP attack lab: fake local SaaS data, real stdio MCP tool boundaries, baseline/defended comparisons, and JSONL evidence. The current live success path uses a NanoClaw group configured with the vulnerable `agentsec-baseline` provider so the attack runs through the real NanoClaw host, CLI, router/session, Docker agent-runner, and MCP server. A direct MCP path is still kept as a secondary harness for isolated debugging.

```bash
uv run agentsec-lab lab manifest --json
uv run agentsec-lab google-mcp run scenarios/google_workspace/gmail_drive_draft_canary.json --mode baseline --out .omo/evidence/google-baseline.jsonl
uv run agentsec-lab google-mcp run scenarios/google_workspace/gmail_drive_draft_canary.json --mode defended --out .omo/evidence/google-defended.jsonl
uv run agentsec-lab google-mcp direct-attack scenarios/google_workspace/gmail_drive_draft_canary.json --mode baseline --out .omo/evidence/direct-mcp-bypass-baseline.jsonl
uv run agentsec-lab google-mcp direct-attack scenarios/google_workspace/gmail_drive_draft_canary.json --mode defended --out .omo/evidence/direct-mcp-bypass-defended.jsonl
uv run agentsec-lab memory-mcp serve-stdio --mode defended --out .omo/evidence/memory-mcp.jsonl
```

The local lab covers fake Gmail, Drive, Memory, and Shopping surfaces. See `docs/local-mcp-attack-lab.md` for the scenario pack, defense layer, optional real-sandbox boundary, and the distinction between the live NanoClaw path and the direct MCP harness.

Generate the current final-demo evidence and summary:

```bash
uv run agentsec-lab lab run-google-demo --out-dir .omo/evidence/final-demo --json
uv run agentsec-lab lab evaluate .omo/evidence/final-demo --json
uv run agentsec-lab lab run-memory-demo --out-dir .omo/evidence/memory-demo --json
uv run agentsec-lab lab evaluate-memory .omo/evidence/memory-demo --json
uv run agentsec-lab lab run-shopping-demo --out-dir .omo/evidence/shopping-demo --json
uv run agentsec-lab lab evaluate-shopping .omo/evidence/shopping-demo --json
uv run agentsec-lab lab run-rag-search-demo --out-dir .omo/evidence/rag-search-demo --json
uv run agentsec-lab lab evaluate-rag-search .omo/evidence/rag-search-demo --json
uv run agentsec-lab lab run-tool-confusion-demo --out-dir .omo/evidence/tool-confusion-demo --json
uv run agentsec-lab lab evaluate-tool-confusion .omo/evidence/tool-confusion-demo --json
uv run agentsec-lab lab run-scenario-pack --out-dir .omo/evidence/scenario-pack-demo --json
uv run agentsec-lab lab evaluate-scenario-pack .omo/evidence/scenario-pack-demo --json
```

The final-demo report is in `docs/nanoclaw-mcp-final-report.ko.md`, and the live presentation script is in `docs/demo-script.ko.md`.

## Controlled Agent Environment

The first agentic AI environment is intentionally controlled and local-only:

- `ScenarioSpec`: typed JSON scenario contract.
- `FakeAgentModel`: deterministic model double with `fake-benign` and `fake-malicious` modes.
- `SafeToolbox`: local-only tools for `read_file` and `send_to_local_sink`.
- `run_scenario`: executes model tool calls and writes JSONL traces.
- `agentsec-lab run`: CLI surface for running one scenario.

Run the seed scenario:

```bash
uv run agentsec-lab run scenarios/seed/file_read_benign.json --model fake-benign --out .omo/evidence/agent-env-benign.jsonl
uv run agentsec-lab run scenarios/seed/file_read_benign.json --model fake-malicious --out .omo/evidence/agent-env-malicious.jsonl
```

The malicious fake model uses only a local sink file. No external network or real credentials are involved.
