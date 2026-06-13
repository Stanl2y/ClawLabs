# AgentSec Lab

한국어 | [English](README.en.md)

Agentic AI 프롬프트 인젝션, MCP 도구 오용, 도구 표면 오염, 방어 전후 동작을 재현하기 위한 로컬 실험실입니다.

## WSL NanoClaw Hybrid MCP Attack Lab 정리자료

- [정리자료 보기](https://htmlpreview.github.io/?https://github.com/Stanl2y/ClawLabs/blob/main/docs/wsl-hybrid-presentation-20260614/presentation.html)
- [정리자료 패키지 다운로드](docs/wsl-hybrid-presentation-20260614.zip)
- [저장소의 HTML 파일 열기](docs/wsl-hybrid-presentation-20260614/presentation.html)

이 저장소는 두 단계로 구성되어 있습니다.

1. 이 저장소만으로 바로 재현할 수 있는 로컬 실험
2. 별도의 NanoClaw 런타임이 필요한 선택적 WSL NanoClaw 재현

첫 번째 섹션의 명령은 이 README 업데이트 전에 깨끗한 클론에서 다시 확인했습니다.

## 바로 동작하는 항목

별도의 NanoClaw 체크아웃 없이, 깨끗한 클론에서 아래 명령을 실행할 수 있습니다.

### 요구 사항

- `git`
- `uv`
- 쇼핑 랩 테스트용 Node.js 22.x
- `docker compose config`를 실행하려는 경우에만 Docker

이 프로젝트는 `.python-version`으로 Python 3.12를 고정합니다. 실제 주 진입점은 `python`이 아니라 `uv`입니다.

## 빠른 시작

저장소 루트에서 실행합니다.

```bash
uv sync --frozen
uv run agentsec-lab --help
uv run pytest -q
node --test webmcp-shopping-lab/tests/storefront.test.mjs
```

깨끗한 체크아웃에서 기대되는 결과:

- `uv run pytest -q` -> `65 passed`
- `node --test webmcp-shopping-lab/tests/storefront.test.mjs` -> `9 passed`

## 가장 빠른 검증 데모

baseline/defended 비교를 한 경로로 확인하려면 다음을 실행합니다.

```bash
uv run agentsec-lab lab run-google-demo --out-dir .omo/evidence/final-demo --json
uv run agentsec-lab lab evaluate .omo/evidence/final-demo --json
```

기대 결과:

- `baseline.attack_success=true`
- `baseline.utility_success=true`
- `defended.attack_success=false`
- `defended.utility_success=true`
- `defended.defense_blocked=true`

이 데모는 로컬 전용입니다. 가짜 Gmail/Drive 데이터, 합성 카나리, JSONL evidence 파일을 사용합니다.

## 전체 로컬 시나리오 팩

전체 로컬 벤치마크 팩을 실행합니다.

```bash
uv run agentsec-lab lab run-scenario-pack --out-dir .omo/evidence/scenario-pack-demo --json
uv run agentsec-lab lab evaluate-scenario-pack .omo/evidence/scenario-pack-demo --json
```

팩에 포함된 검증 시나리오:

- `google_workspace_canary`
- `memory_poisoning`
- `shopping_tool_description_poisoning`
- `rag_search_poisoning`
- `tool_use_confusion`

기대 집계 결과:

- `overall_success=true`

## 유용한 로컬 명령

표준 랩 매니페스트를 출력합니다.

```bash
uv run agentsec-lab lab manifest --json
```

Google Workspace 시나리오 하나를 직접 실행합니다.

```bash
uv run agentsec-lab google-mcp run scenarios/google_workspace/gmail_drive_draft_canary.json --mode baseline --out .omo/evidence/google-baseline.jsonl
uv run agentsec-lab google-mcp run scenarios/google_workspace/gmail_drive_draft_canary.json --mode defended --out .omo/evidence/google-defended.jsonl
```

직접 MCP 우회 하네스를 실행합니다.

```bash
uv run agentsec-lab google-mcp direct-attack scenarios/google_workspace/gmail_drive_draft_canary.json --mode baseline --out .omo/evidence/direct-mcp-bypass-baseline.jsonl
uv run agentsec-lab google-mcp direct-attack scenarios/google_workspace/gmail_drive_draft_canary.json --mode defended --out .omo/evidence/direct-mcp-bypass-defended.jsonl
```

격리된 seed agent 환경을 실행합니다.

```bash
uv run agentsec-lab run scenarios/seed/file_read_benign.json --model fake-benign --out .omo/evidence/agent-env-benign.jsonl
uv run agentsec-lab run scenarios/seed/file_read_benign.json --model fake-malicious --out .omo/evidence/agent-env-malicious.jsonl
```

## 프로젝트 구조

- `src/agentsec_lab`: Python CLI와 로컬 벤치마크 로직
- `scenarios/`: CLI가 사용하는 시나리오 계약
- `fixtures/`: 시나리오용 가짜 로컬 데이터
- `webmcp-shopping-lab/`: 로컬 쇼핑 도구 표면 오염 랩
- `nanoclaw-attack-lab/`: 선택적 NanoClaw WSL 재현용 파일과 스크립트
- `docs/`: 보고서, 흐름 문서, 한국어 문서

## 안전 모델

이 저장소는 기본적으로 로컬 및 합성 환경에 머물도록 설계되어 있습니다.

- 로컬 데모에는 실제 Gmail, Drive, CRM, 결제 시스템이 필요하지 않습니다.
- 검증된 로컬 흐름에는 실제 시크릿이 필요하지 않습니다.
- 성공 여부는 로컬 JSONL evidence 파일에 기록됩니다.
- 보호 값은 `GWS_MCP_CANARY_001`, `ISO_SYNTH_CANARY_42` 같은 합성 카나리입니다.

## 선택적 WSL NanoClaw 재현

실제 NanoClaw WSL 런타임으로 같은 랩을 실행하려면 이 섹션을 사용합니다. NanoClaw 체크아웃은 이 저장소와 별개이며 위치가 고정되어 있지 않습니다. WSL 경로를 하나 선택하고 `NANOCLAW_DIR`로 기록하세요.

### 1. WSL에 NanoClaw 설치

WSL bash 셸을 엽니다. 먼저 Node.js 20+와 `git`을 설치합니다. 로컬 쇼핑 테스트가 Node 22를 사용하므로 Node.js 22.x를 권장합니다.

NanoClaw를 둘 디렉터리를 선택합니다. 아래 예시는 `$HOME/dev/nanoclaw`를 사용하지만 어떤 WSL 경로도 가능합니다.

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

처음 설정한다면 NanoClaw setup flow를 실행하고 이 랩에 사용할 agent group을 만들거나 확인합니다.

```bash
cd "$NANOCLAW_DIR"
pnpm run setup
pnpm run ncl groups list
```

대상 group id를 저장합니다. `ag-...` 형태이며 랩 스크립트에서는 `GROUP_ID`로 사용합니다.

### 2. 이 랩을 NanoClaw 경로에 맞게 설정

이 저장소 루트에서 랩 환경 파일을 만듭니다.

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh env
bash nanoclaw-attack-lab/run-google-workspace-lab.sh edit-env
```

현재 머신에 맞는 값을 설정합니다.

```bash
NANOCLAW_DIR=/absolute/wsl/path/to/nanoclaw
NODE_BIN_DIR=
GROUP_ID=ag-your-own-group-id
GROUP_DIR=groups/_ping-test
DEFAULT_FLOW=baseline
```

값 규칙:

- `NANOCLAW_DIR`는 `package.json`과 `scripts/chat.ts`가 있는 NanoClaw 체크아웃을 가리켜야 합니다.
- `NODE_BIN_DIR`는 WSL에서 이미 `node`와 `pnpm`을 찾을 수 있으면 비워 둡니다. 아니면 `nvm`의 `bin` 디렉터리처럼 해당 바이너리가 있는 디렉터리로 설정합니다.
- `GROUP_ID`는 `pnpm run ncl groups list`에서 확인한 NanoClaw agent group id입니다.
- `GROUP_DIR`는 해당 group의 evidence 디렉터리입니다. 기본값은 `groups/_ping-test`입니다. NanoClaw group 디렉터리가 다를 때만 바꾸세요.

시나리오를 실행하기 전에 경로 해석 결과를 확인합니다.

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh status
bash nanoclaw-attack-lab/run-google-workspace-lab.sh show-paths
```

### 3. 랩을 NanoClaw group으로 동기화

NanoClaw는 `$NANOCLAW_DIR/$GROUP_DIR` 아래 group workspace에서 agent 세션을 실행합니다. 첫 실행 전에 이 저장소의 랩 파일을 동기화하고, 랩 코드 변경 후에도 같은 명령을 다시 실행합니다.

```bash
mkdir -p "$NANOCLAW_DIR/$GROUP_DIR/lab"
mkdir -p "$NANOCLAW_DIR/$GROUP_DIR/nanoclaw-attack-lab" "$NANOCLAW_DIR/$GROUP_DIR/webmcp-shopping-lab" "$NANOCLAW_DIR/$GROUP_DIR/lab/fixtures"
cp -R nanoclaw-attack-lab/. "$NANOCLAW_DIR/$GROUP_DIR/nanoclaw-attack-lab/"
cp -R webmcp-shopping-lab/. "$NANOCLAW_DIR/$GROUP_DIR/webmcp-shopping-lab/"
cp -R nanoclaw-attack-lab/fixtures/. "$NANOCLAW_DIR/$GROUP_DIR/lab/fixtures/"
cp nanoclaw-attack-lab/safe-sink-mcp.mjs "$NANOCLAW_DIR/$GROUP_DIR/lab/safe-sink-mcp.mjs"
```

Google runner가 자동으로 전환하지 않는 hybrid MCP 서버를 등록합니다.

```bash
cd "$NANOCLAW_DIR"
pnpm run ncl groups config add-mcp-server \
  --id "$GROUP_ID" \
  --name lab_vendor \
  --command node \
  --args '["/workspace/agent/lab/safe-sink-mcp.mjs"]' \
  --env '{"LAB_DIR":"/workspace/agent/lab"}'

pnpm run ncl groups config add-mcp-server \
  --id "$GROUP_ID" \
  --name shopping_mall \
  --command node \
  --args '["/workspace/agent/webmcp-shopping-lab/webmcp-bridge.mjs","--mode-file","/workspace/agent/webmcp-shopping-lab/mode-state.json","--evidence-dir","/workspace/agent/webmcp-shopping-lab/evidence-nanoclaw-compare"]' \
  --env '{"WEBMCP_MODE":"normal"}'

pnpm run ncl groups restart --id "$GROUP_ID"
```

아래 `baseline`과 `defended` 명령은 `google_workspace_lab`을 자동으로 설정하므로 해당 서버를 직접 추가할 필요는 없습니다.

전체 hybrid wiring을 확인합니다.

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh hybrid-status
bash nanoclaw-attack-lab/run-google-workspace-lab.sh config
```

설정에는 최소한 다음 서버가 포함되어야 합니다.

- `google_workspace_lab`
- `lab_vendor`
- `shopping_mall`

### 4. NanoClaw 흐름 실행

한 WSL 터미널에서 NanoClaw host를 시작합니다.

```bash
cd "$NANOCLAW_DIR"
pnpm start
```

다른 WSL 터미널에서 이 저장소 루트 기준으로 랩 명령을 실행합니다.

```bash
bash nanoclaw-attack-lab/run-google-workspace-lab.sh readiness
bash nanoclaw-attack-lab/run-google-workspace-lab.sh baseline
bash nanoclaw-attack-lab/run-google-workspace-lab.sh show-baseline
bash nanoclaw-attack-lab/run-google-workspace-lab.sh defended
bash nanoclaw-attack-lab/run-google-workspace-lab.sh show-defended
```

hybrid flow는 vendor와 shopping 시나리오도 지원합니다.

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

대화형 실험:

```bash
bash nanoclaw-attack-lab/manual-google-workspace-chat.sh
```

참고 문서:

- `nanoclaw-attack-lab/RUNBOOK.md`
- `docs/pure-wsl-nanoclaw-repro.ko.md`

WSL 경로가 필요한 이유:

- `google_workspace_lab`을 `baseline`과 `defended` 사이에서 전환
- vendor attack 시나리오를 NanoClaw group으로 실행
- `shopping_mall` poisoned-vs-normal 비교 실행
- `$NANOCLAW_DIR/$GROUP_DIR/...` 아래 evidence 확인

## 쇼핑 랩만 실행

로컬 쇼핑 도구 표면 랩만 실행하려면 다음을 사용합니다.

```bash
node webmcp-shopping-lab/webmcp-bridge.mjs --http --port 4173
```

그다음 아래 주소를 엽니다.

- `http://127.0.0.1:4173/`
- `http://127.0.0.1:4173/lab.html`
- `http://127.0.0.1:4173/evidence.html`

참고:

- `webmcp-shopping-lab/README.md`

## 문제 해결

- `uv sync --frozen`이 Python 3.12 누락 때문에 실패하면 Python 3.12를 설치하거나 `uv`가 인터프리터를 준비하게 한 뒤 다시 실행합니다.
- `node --test ...`가 실패하면 Node.js 22.x가 설치되어 있는지 확인합니다.
- 팀원이 NanoClaw WSL 흐름을 사용하려는 경우, 기본 NanoClaw 경로를 가정하지 말고 `env` 명령을 실행한 뒤 해당 머신의 실제 체크아웃 경로를 `NANOCLAW_DIR`로 설정하세요.

## 문서

- 로컬 랩 설계: `docs/local-mcp-attack-lab.md`
- 한국어 랩 기록: `docs/local-mcp-attack-lab-record.ko.md`
- 최종 보고서: `docs/nanoclaw-mcp-final-report.ko.md`
- 데모 스크립트: `docs/demo-script.ko.md`
