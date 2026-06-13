# AgentSec Lab

Reproducible local lab for studying agentic AI prompt injection, MCP tool misuse, tool-surface poisoning, and defended-vs-baseline behavior.

This repository is split into two levels:

1. Immediate local reproduction from this repo alone
2. Optional WSL NanoClaw reproduction, which needs a separate NanoClaw runtime

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

Use this section when you want to run the same lab through a real NanoClaw WSL runtime. The NanoClaw checkout is separate from this repository, and its location is not fixed. Pick any WSL path and record it as `NANOCLAW_DIR`.

### 1. Install NanoClaw In WSL

Open a WSL bash shell. Install Node.js 20+ and `git` first. Node.js 22.x is recommended because the local shopping tests use Node 22.

Choose a directory for NanoClaw. This example uses `$HOME/dev/nanoclaw`, but any WSL path is valid:

```bash
export NANOCLAW_DIR="$HOME/dev/nanoclaw"
mkdir -p "$(dirname "$NANOCLAW_DIR")"
git clone https://github.com/nanocoai/nanoclaw.git "$NANOCLAW_DIR"
cd "$NANOCLAW_DIR"
corepack enable
corepack prepare pnpm@10.33.0 --activate
pnpm install
pnpm run build
```

For a first-time NanoClaw setup, run the NanoClaw setup flow and create or identify the agent group you will use for this lab:

```bash
cd "$NANOCLAW_DIR"
pnpm run setup
pnpm run ncl groups list
```

Save the target group id. It should look like `ag-...`; the lab scripts use it as `GROUP_ID`.

### 2. Configure This Lab For Your NanoClaw Path

From this repository root, create the lab environment file:

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh env
bash nanoclaw-attack-lab/run-google-workspace-lab.sh edit-env
```

Set values for the current machine:

```bash
NANOCLAW_DIR=/absolute/wsl/path/to/nanoclaw
NODE_BIN_DIR=
GROUP_ID=ag-your-own-group-id
GROUP_DIR=groups/_ping-test
DEFAULT_FLOW=baseline
```

Rules for these values:

- `NANOCLAW_DIR` must point to the NanoClaw checkout that contains `package.json` and `scripts/chat.ts`.
- `NODE_BIN_DIR` can stay empty if WSL can already find `node` and `pnpm`; otherwise set it to the directory containing those binaries, such as an `nvm` `bin` directory.
- `GROUP_ID` is the NanoClaw agent group id from `pnpm run ncl groups list`.
- `GROUP_DIR` is the evidence directory for that group. The scripts default to `groups/_ping-test`; change it only if your NanoClaw group directory differs.

Check the resolved paths before running scenarios:

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh status
bash nanoclaw-attack-lab/run-google-workspace-lab.sh show-paths
```

### 3. Run The NanoClaw Flow

Start the NanoClaw host in one WSL terminal:

```bash
cd "$NANOCLAW_DIR"
pnpm start
```

In another WSL terminal, run the lab commands from this repository root:

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh readiness
bash nanoclaw-attack-lab/run-google-workspace-lab.sh baseline
bash nanoclaw-attack-lab/run-google-workspace-lab.sh show-baseline
bash nanoclaw-attack-lab/run-google-workspace-lab.sh defended
bash nanoclaw-attack-lab/run-google-workspace-lab.sh show-defended
```

The hybrid flow also supports the vendor and shopping scenarios:

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh hybrid-status
bash nanoclaw-attack-lab/run-google-workspace-lab.sh lab-document
bash nanoclaw-attack-lab/run-google-workspace-lab.sh lab-tool-poisoning
bash nanoclaw-attack-lab/run-google-workspace-lab.sh lab-response-injection
bash nanoclaw-attack-lab/run-google-workspace-lab.sh lab-tool-confusion
bash nanoclaw-attack-lab/run-google-workspace-lab.sh lab-rag
bash nanoclaw-attack-lab/run-google-workspace-lab.sh lab-skill
bash nanoclaw-attack-lab/run-google-workspace-lab.sh shopping-normal
bash nanoclaw-attack-lab/run-google-workspace-lab.sh shopping-poisoned
```

For interactive experimentation:

```bash
bash nanoclaw-attack-lab/manual-google-workspace-chat.sh
```

Reference docs:

- `nanoclaw-attack-lab/RUNBOOK.md`
- `docs/pure-wsl-nanoclaw-repro.ko.md`

What the WSL path is for:

- switching `google_workspace_lab` between `baseline` and `defended`
- running the vendor attack scenarios through the NanoClaw group
- running the `shopping_mall` poisoned-vs-normal comparison
- checking evidence under `$NANOCLAW_DIR/$GROUP_DIR/...`

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
- If a teammate wants the NanoClaw WSL flow, do not assume any default NanoClaw path; run the `env` command and set `NANOCLAW_DIR` to that machine's actual checkout.

## Documentation

- Local lab design: `docs/local-mcp-attack-lab.md`
- Korean lab record: `docs/local-mcp-attack-lab-record.ko.md`
- Final report: `docs/nanoclaw-mcp-final-report.ko.md`
- Demo script: `docs/demo-script.ko.md`
