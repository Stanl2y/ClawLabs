# AgentSec Lab

Reproducible local lab for studying agentic AI prompt injection, MCP tool misuse, tool-surface poisoning, and defended-vs-baseline behavior.

This repository is split into two levels:

1. Immediate local reproduction from this repo alone
2. Optional WSL NanoClaw reproduction, which needs a separate `~/labs/nanoclaw` runtime

The commands in the first section were re-verified from a fresh clone before this README update.

## What Works Immediately

These commands work from a fresh clone of this repository without a separate NanoClaw checkout.

### Requirements

- `git`
- `uv`
- Node.js 22.x for the shopping lab tests
- Docker only if you want to run `docker compose config`

This project is pinned to Python 3.12 through `.python-version`. In practice, the main entrypoint is `uv`, not `python`.

## Quick Start

From the repository root:

```bash
uv sync --frozen
uv run agentsec-lab --help
uv run pytest -q
node --test webmcp-shopping-lab/tests/storefront.test.mjs
```

Expected results on a clean checkout:

- `uv run pytest -q` -> `65 passed`
- `node --test webmcp-shopping-lab/tests/storefront.test.mjs` -> `9 passed`

## Fastest Verified Demo

If you want one command path that proves the baseline/defended comparison immediately:

```bash
uv run agentsec-lab lab run-google-demo --out-dir .omo/evidence/final-demo --json
uv run agentsec-lab lab evaluate .omo/evidence/final-demo --json
```

What this should show:

- `baseline.attack_success=true`
- `baseline.utility_success=true`
- `defended.attack_success=false`
- `defended.utility_success=true`
- `defended.defense_blocked=true`

This demo is local-only. It uses fake Gmail/Drive data, synthetic canaries, and JSONL evidence files.

## Full Local Scenario Pack

Run the full local benchmark pack:

```bash
uv run agentsec-lab lab run-scenario-pack --out-dir .omo/evidence/scenario-pack-demo --json
uv run agentsec-lab lab evaluate-scenario-pack .omo/evidence/scenario-pack-demo --json
```

Verified scenarios in the pack:

- `google_workspace_canary`
- `memory_poisoning`
- `shopping_tool_description_poisoning`
- `rag_search_poisoning`
- `tool_use_confusion`

Expected aggregate result:

- `overall_success=true`

## Useful Local Commands

Print the canonical lab manifest:

```bash
uv run agentsec-lab lab manifest --json
```

Run one Google Workspace scenario directly:

```bash
uv run agentsec-lab google-mcp run scenarios/google_workspace/gmail_drive_draft_canary.json --mode baseline --out .omo/evidence/google-baseline.jsonl
uv run agentsec-lab google-mcp run scenarios/google_workspace/gmail_drive_draft_canary.json --mode defended --out .omo/evidence/google-defended.jsonl
```

Run the direct MCP bypass harness:

```bash
uv run agentsec-lab google-mcp direct-attack scenarios/google_workspace/gmail_drive_draft_canary.json --mode baseline --out .omo/evidence/direct-mcp-bypass-baseline.jsonl
uv run agentsec-lab google-mcp direct-attack scenarios/google_workspace/gmail_drive_draft_canary.json --mode defended --out .omo/evidence/direct-mcp-bypass-defended.jsonl
```

Run the isolated seed agent environment:

```bash
uv run agentsec-lab run scenarios/seed/file_read_benign.json --model fake-benign --out .omo/evidence/agent-env-benign.jsonl
uv run agentsec-lab run scenarios/seed/file_read_benign.json --model fake-malicious --out .omo/evidence/agent-env-malicious.jsonl
```

## Project Layout

- `src/agentsec_lab`: Python CLI and local benchmark logic
- `scenarios/`: scenario contracts used by the CLI
- `fixtures/`: fake local data used by the scenarios
- `webmcp-shopping-lab/`: local shopping tool-surface poisoning lab
- `nanoclaw-attack-lab/`: files and scripts for the optional NanoClaw WSL reproduction
- `docs/`: reports, flow writeups, and Korean documentation

## Safety Model

This repository is designed to stay local and synthetic by default.

- No real Gmail, Drive, CRM, or payment system is required for the local demos
- No real secrets are needed for the verified local flows
- Success is recorded in local JSONL evidence files
- Protected values are synthetic canaries such as `GWS_MCP_CANARY_001` and `ISO_SYNTH_CANARY_42`

## Optional WSL NanoClaw Reproduction

This section is not "clone and run". It needs a separate NanoClaw runtime already prepared in WSL.

Required extra environment:

- WSL
- a working NanoClaw checkout at `~/labs/nanoclaw`
- WSL `node` and `pnpm`
- a configured NanoClaw group for the hybrid lab flow

The main entry scripts in this repository for that flow are:

- `nanoclaw-attack-lab/run-google-workspace-lab.sh`
- `nanoclaw-attack-lab/manual-google-workspace-chat.sh`

The wrapper scripts forward to:

- `nanoclaw-attack-lab/wsl-only-run-google-workspace.sh`
- `nanoclaw-attack-lab/wsl-only-manual-chat.sh`
- `nanoclaw-attack-lab/wsl-only-hybrid-lib.sh`

Reference docs:

- `nanoclaw-attack-lab/RUNBOOK.md`
- `docs/pure-wsl-nanoclaw-repro.ko.md`

What the WSL path is for:

- switching `google_workspace_lab` between `baseline` and `defended`
- running the vendor attack scenarios through the NanoClaw group
- running the `shopping_mall` poisoned-vs-normal comparison
- checking evidence under `~/labs/nanoclaw/groups/_ping-test/...`

## Shopping Lab Only

If someone wants only the local shopping tool-surface lab:

```bash
node webmcp-shopping-lab/webmcp-bridge.mjs --http --port 4173
```

Then open:

- `http://127.0.0.1:4173/`
- `http://127.0.0.1:4173/lab.html`
- `http://127.0.0.1:4173/evidence.html`

Reference:

- `webmcp-shopping-lab/README.md`

## Troubleshooting

- If `uv sync --frozen` fails because Python 3.12 is missing, install Python 3.12 or let `uv` provision the interpreter, then rerun `uv sync --frozen`.
- If `node --test ...` fails, check that Node.js 22.x is installed.
- If a teammate wants the NanoClaw WSL flow, do not start from this repository alone; start from the WSL guide in `docs/pure-wsl-nanoclaw-repro.ko.md`.

## Documentation

- Local lab design: `docs/local-mcp-attack-lab.md`
- Korean lab record: `docs/local-mcp-attack-lab-record.ko.md`
- Final report: `docs/nanoclaw-mcp-final-report.ko.md`
- Demo script: `docs/demo-script.ko.md`
