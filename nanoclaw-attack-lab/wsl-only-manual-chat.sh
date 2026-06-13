#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNER="$SCRIPT_DIR/run-google-workspace.sh"
DEFAULT_NANOCLAW_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
ENV_PATH="${NANOCLAW_ENV:-$LAB_DIR/.env}"

load_env() {
  [[ -f "$ENV_PATH" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
    local key="${line%%=*}"
    local value="${line#*=}"
    key="${key//[[:space:]]/}"
    case "$key" in
      NANOCLAW_DIR|NODE_BIN_DIR|GROUP_ID|DEFAULT_FLOW)
        export "$key=$value"
        ;;
    esac
  done < "$ENV_PATH"
}

write_default_env() {
  if [[ -f "$ENV_PATH" ]]; then
    echo "$ENV_PATH"
    return 0
  fi
  cat > "$ENV_PATH" <<EOF_ENV
NANOCLAW_DIR=$DEFAULT_NANOCLAW_DIR
NODE_BIN_DIR=$HOME/.nvm/versions/node/v22.20.0/bin
GROUP_ID=ag-1780974144312-4bw6ax
DEFAULT_FLOW=baseline
EOF_ENV
  echo "$ENV_PATH"
}

load_env

NANOCLAW_DIR="${NANOCLAW_DIR:-$DEFAULT_NANOCLAW_DIR}"
NODE_BIN_DIR="${NODE_BIN_DIR:-$HOME/.nvm/versions/node/v22.20.0/bin}"

require_repo() {
  if [[ ! -d "$NANOCLAW_DIR" ]]; then
    echo "NanoClaw repo not found: $NANOCLAW_DIR" >&2
    exit 1
  fi
}

use_node() {
  export PATH="$NODE_BIN_DIR:$PATH"
  if ! command -v node >/dev/null 2>&1; then
    echo "node not found. Set NODE_BIN_DIR in $ENV_PATH." >&2
    exit 1
  fi
  if ! command -v pnpm >/dev/null 2>&1; then
    echo "pnpm not found. Set NODE_BIN_DIR in $ENV_PATH." >&2
    exit 1
  fi
}

send_prompt() {
  local prompt="$1"
  (
    cd "$NANOCLAW_DIR"
    pnpm run chat "$prompt"
  )
}

run_shortcut() {
  case "$1" in
    /readiness) "$RUNNER" readiness ;;
    /baseline) "$RUNNER" baseline ;;
    /defended) "$RUNNER" defended ;;
    /hybrid-status) "$RUNNER" hybrid-status ;;
    /google-baseline) "$RUNNER" google-baseline ;;
    /google-defended) "$RUNNER" google-defended ;;
    /document|/lab-document) "$RUNNER" lab-document ;;
    /tool-poison|/lab-tool-poisoning) "$RUNNER" lab-tool-poisoning ;;
    /response-injection|/lab-response-injection) "$RUNNER" lab-response-injection ;;
    /tool-confusion|/lab-tool-confusion) "$RUNNER" lab-tool-confusion ;;
    /rag|/lab-rag) "$RUNNER" lab-rag ;;
    /skill|/lab-skill) "$RUNNER" lab-skill ;;
    /shop-normal|/shopping-normal) "$RUNNER" shopping-normal ;;
    /shop-poison|/shopping-poisoned) "$RUNNER" shopping-poisoned ;;
    /lab-evidence) "$RUNNER" show-lab-evidence ;;
    /shop-mode) "$RUNNER" show-shopping-mode ;;
    /shop-evidence) "$RUNNER" show-shopping-evidence ;;
    /shop-tool-surface) "$RUNNER" show-shopping-tool-surface ;;
    /reset-evidence) "$RUNNER" reset-hybrid-evidence ;;
    /clear-chat) "$RUNNER" clear-chat ;;
    /run) "$RUNNER" run ;;
    /edit) "$RUNNER" edit-env ;;
    /env) "$RUNNER" env ;;
    /status) "$RUNNER" status ;;
    /help) print_help ;;
    *) return 1 ;;
  esac
}

print_help() {
  cat <<EOF_HELP
Manual pure WSL NanoClaw chat

Usage from ~/labs/nanoclaw:
  bash ./manual-google-workspace-chat.sh
  bash ./manual-google-workspace-chat.sh "your prompt"
  bash ./manual-google-workspace-chat.sh /run

Interactive shortcuts:
  /readiness  connection check
  /baseline   natural baseline flow
  /defended   natural defended flow
  /hybrid-status  show Google/lab/shopping wiring
  /google-baseline /google-defended
  /document   vendor document injection
  /tool-poison  tool description poisoning
  /response-injection  tool response injection
  /tool-confusion  tool-use confusion
  /rag        retrieved-note poisoning
  /skill      helper-skill injection
  /shop-normal /shop-poison
  /lab-evidence /shop-mode /shop-evidence /shop-tool-surface
  /reset-evidence
  /clear-chat  reset the NanoClaw CLI chat context
  /clear      raw NanoClaw session reset command
  /run        run DEFAULT_FLOW from .env
  /edit       open .env
  /env        create/print .env path
  /status     show current config
  /help
  /exit

Environment file:
  $ENV_PATH
EOF_HELP
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${1:-}" == "help" ]]; then
  print_help
  exit 0
fi

require_repo
use_node

if [[ $# -gt 0 ]]; then
  if ! run_shortcut "$*"; then
    send_prompt "$*"
  fi
  exit 0
fi

write_default_env >/dev/null

cat <<EOF_INTRO
NanoClaw repo: $NANOCLAW_DIR
Node bin dir: $NODE_BIN_DIR
Env file: $ENV_PATH

Type your prompt and press Enter.
Shortcuts:
  /readiness /baseline /defended /hybrid-status
  /document /tool-poison /response-injection /tool-confusion /rag /skill
  /shop-normal /shop-poison /lab-evidence /shop-mode /shop-evidence /shop-tool-surface
  /clear-chat /run /edit /env /status /help /exit
EOF_INTRO

while true; do
  printf '\nprompt> '
  if ! IFS= read -r input; then
    printf '\n'
    break
  fi
  case "$input" in
    "") continue ;;
    /exit|exit|quit) break ;;
    /readiness|/baseline|/defended|/hybrid-status|/google-baseline|/google-defended|/document|/lab-document|/tool-poison|/lab-tool-poisoning|/response-injection|/lab-response-injection|/tool-confusion|/lab-tool-confusion|/rag|/lab-rag|/skill|/lab-skill|/shop-normal|/shopping-normal|/shop-poison|/shopping-poisoned|/lab-evidence|/shop-mode|/shop-evidence|/shop-tool-surface|/reset-evidence|/clear-chat|/run|/edit|/env|/status|/help) run_shortcut "$input" ;;
    *) send_prompt "$input" ;;
  esac
done
