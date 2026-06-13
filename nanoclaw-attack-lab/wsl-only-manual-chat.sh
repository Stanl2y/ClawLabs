#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_PATH="${NANOCLAW_ENV:-$LAB_DIR/.env}"

is_nanoclaw_dir() {
  local candidate="$1"
  [[ -n "$candidate" && -f "$candidate/package.json" && -f "$candidate/scripts/chat.ts" ]]
}

detect_runner() {
  if [[ -x "$SCRIPT_DIR/run-google-workspace-lab.sh" || -f "$SCRIPT_DIR/run-google-workspace-lab.sh" ]]; then
    printf '%s\n' "$SCRIPT_DIR/run-google-workspace-lab.sh"
    return 0
  fi
  printf '%s\n' "$SCRIPT_DIR/wsl-only-run-google-workspace.sh"
}

detect_default_nanoclaw_dir() {
  local candidate
  for candidate in "$LAB_DIR" "$(cd "$SCRIPT_DIR/../../../.." 2>/dev/null && pwd)" "$HOME/labs/nanoclaw" "$PWD"; do
    if is_nanoclaw_dir "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  printf '%s\n' "$HOME/labs/nanoclaw"
}

detect_default_node_bin_dir() {
  if command -v node >/dev/null 2>&1; then
    dirname "$(command -v node)"
    return 0
  fi
  if [[ -d "$HOME/.nvm/versions/node" ]]; then
    find "$HOME/.nvm/versions/node" -mindepth 2 -maxdepth 2 -type f -name node -path '*/bin/node' 2>/dev/null | sort -V | tail -n 1 | xargs -r dirname
    return 0
  fi
  printf '\n'
}

RUNNER="$(detect_runner)"
DEFAULT_NANOCLAW_DIR="$(detect_default_nanoclaw_dir)"
DEFAULT_NODE_BIN_DIR="$(detect_default_node_bin_dir)"
DEFAULT_GROUP_DIR="groups/_ping-test"

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
      NANOCLAW_DIR|NODE_BIN_DIR|GROUP_ID|GROUP_DIR|DEFAULT_FLOW)
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
NODE_BIN_DIR=$DEFAULT_NODE_BIN_DIR
GROUP_ID=
GROUP_DIR=$DEFAULT_GROUP_DIR
DEFAULT_FLOW=baseline
EOF_ENV
  echo "$ENV_PATH"
}

load_env

NANOCLAW_DIR="${NANOCLAW_DIR:-$DEFAULT_NANOCLAW_DIR}"
NODE_BIN_DIR="${NODE_BIN_DIR:-$DEFAULT_NODE_BIN_DIR}"

require_repo() {
  if ! is_nanoclaw_dir "$NANOCLAW_DIR"; then
    echo "NanoClaw repo not found or invalid: $NANOCLAW_DIR" >&2
    echo "Set NANOCLAW_DIR in $ENV_PATH to the directory that contains package.json and scripts/chat.ts." >&2
    exit 1
  fi
}

use_node() {
  if [[ -n "$NODE_BIN_DIR" ]]; then
    export PATH="$NODE_BIN_DIR:$PATH"
  fi
  if ! command -v node >/dev/null 2>&1; then
    echo "node not found. Install Node in WSL or set NODE_BIN_DIR in $ENV_PATH." >&2
    exit 1
  fi
  if ! command -v pnpm >/dev/null 2>&1; then
    echo "pnpm not found. Install pnpm in WSL or set NODE_BIN_DIR in $ENV_PATH." >&2
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
    /readiness) bash "$RUNNER" readiness ;;
    /baseline) bash "$RUNNER" baseline ;;
    /defended) bash "$RUNNER" defended ;;
    /hybrid-status) bash "$RUNNER" hybrid-status ;;
    /google-baseline) bash "$RUNNER" google-baseline ;;
    /google-defended) bash "$RUNNER" google-defended ;;
    /document|/lab-document) bash "$RUNNER" lab-document ;;
    /tool-poison|/lab-tool-poisoning) bash "$RUNNER" lab-tool-poisoning ;;
    /response-injection|/lab-response-injection) bash "$RUNNER" lab-response-injection ;;
    /tool-confusion|/lab-tool-confusion) bash "$RUNNER" lab-tool-confusion ;;
    /rag|/lab-rag) bash "$RUNNER" lab-rag ;;
    /skill|/lab-skill) bash "$RUNNER" lab-skill ;;
    /shop-normal|/shopping-normal) bash "$RUNNER" shopping-normal ;;
    /shop-poison|/shopping-poisoned) bash "$RUNNER" shopping-poisoned ;;
    /lab-evidence) bash "$RUNNER" show-lab-evidence ;;
    /shop-mode) bash "$RUNNER" show-shopping-mode ;;
    /shop-evidence) bash "$RUNNER" show-shopping-evidence ;;
    /shop-tool-surface) bash "$RUNNER" show-shopping-tool-surface ;;
    /reset-evidence) bash "$RUNNER" reset-hybrid-evidence ;;
    /clear-chat) bash "$RUNNER" clear-chat ;;
    /run) bash "$RUNNER" run ;;
    /edit) bash "$RUNNER" edit-env ;;
    /env) bash "$RUNNER" env ;;
    /status) bash "$RUNNER" status ;;
    /help) print_help ;;
    *) return 1 ;;
  esac
}

print_help() {
  cat <<EOF_HELP
Manual pure WSL NanoClaw chat

Usage:
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

For non-default NanoClaw installs, run:
  bash ./run-google-workspace-lab.sh env
  bash ./run-google-workspace-lab.sh edit-env
and set NANOCLAW_DIR, GROUP_ID, GROUP_DIR, and NODE_BIN_DIR.
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
