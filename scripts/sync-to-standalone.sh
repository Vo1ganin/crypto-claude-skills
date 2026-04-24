#!/usr/bin/env bash
# Sync a single skill from the umbrella repo into its standalone repo.
#
# Usage:
#   ./scripts/sync-to-standalone.sh <skill>            # sync + commit + push
#   ./scripts/sync-to-standalone.sh <skill> --init     # first-time: create github repo too
#   ./scripts/sync-to-standalone.sh --all [--init]     # sync all four skills
#
# Layout:
#   Umbrella lives in: <repo-root> (the dir containing this script's parent)
#   Standalone repos cloned to: ../standalone-builds/<skill-standalone-name>

set -euo pipefail

GITHUB_USER="Vo1ganin"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/standalone-builds"
mkdir -p "$BUILD_DIR"

# Meta (POSIX-portable, no associative arrays — works on default macOS bash 3.2)
# skill|repo_name|docs_folder|description
skill_meta() {
  case "$1" in
    dune)
      echo "dune-skill|dune|Claude Code skill for Dune Analytics SQL across 100+ chains — with credit budget rules and FREE/PAID key rotation"
      ;;
    solscan)
      echo "solscan-skill|solscan|Claude Code skill for Solscan Pro v2 API — async batch patterns, export endpoints, live CU monitoring"
      ;;
    nansen)
      echo "nansen-skill|nansen|Claude Code skill for Nansen API — Smart Money + wallet profiling across 37 chains, credit-trap aware"
      ;;
    solana-rpc)
      echo "solana-rpc-skill|quicknode|Claude Code skill for Solana JSON-RPC — universal (Helius/QuickNode/any), batched, enhanced APIs"
      ;;
    *)
      echo "ERROR: unknown skill: $1" >&2
      return 1
      ;;
  esac
}

write_env_example() {
  local skill="$1" target="$2"
  case "$skill" in
    dune)
      cat > "$target/.env.example" <<'EOF'
# Copy to .env and fill with your real keys. Never commit .env.

# Free key (default)
DUNE_API_KEY_FREE=

# Additional free keys for rotation (optional)
# DUNE_API_KEY_FREE_2=

# Paid key (for bulk exports, optional)
# DUNE_API_KEY_PAID=
EOF
      ;;
    solscan)
      cat > "$target/.env.example" <<'EOF'
# Copy to .env and fill with your real key. Never commit .env.
SOLSCAN_API_KEY=
EOF
      ;;
    nansen)
      cat > "$target/.env.example" <<'EOF'
# Copy to .env and fill with your real key. Never commit .env.
NANSEN_API_KEY=

# Optional multi-key rotation
# NANSEN_API_KEY_2=
EOF
      ;;
    solana-rpc)
      cat > "$target/.env.example" <<'EOF'
# Copy to .env and fill with your provider URL. Never commit .env.
# Examples:
#   Helius:    https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
#   QuickNode: https://YOUR-NAME.solana-mainnet.quiknode.pro/YOUR-TOKEN/
#   Ankr:      https://rpc.ankr.com/solana/YOUR_KEY
SOLANA_RPC_URL=

# Optional primary/fallback setup
# SOLANA_RPC_URL_PRIMARY=
# SOLANA_RPC_URL_FALLBACK=
EOF
      ;;
  esac
}

sync_skill() {
  local skill="$1"
  local init="${2:-}"

  local meta repo_name docs desc
  meta="$(skill_meta "$skill")"
  repo_name="$(echo "$meta" | cut -d'|' -f1)"
  docs="$(echo "$meta" | cut -d'|' -f2)"
  desc="$(echo "$meta" | cut -d'|' -f3)"

  local target="$BUILD_DIR/$repo_name"

  echo ""
  echo "═══ [$skill → $repo_name] ═══"

  if [[ "$init" == "--init" ]] || [[ ! -d "$target/.git" ]]; then
    rm -rf "$target"
    mkdir -p "$target"
    cd "$target"
    git init -q -b main
    git config user.email "$(cd "$REPO_ROOT" && git config user.email)"
    git config user.name "$(cd "$REPO_ROOT" && git config user.name)"
  else
    cd "$target"
    git checkout -q main
    git pull -q --rebase --autostash origin main 2>/dev/null || true
  fi

  # --- Copy skill content ---
  rm -rf references SKILL.md
  cp -R "$REPO_ROOT/skills/$skill/"* "$target/"

  # --- Copy docs corpus ---
  mkdir -p "$target/docs"
  rm -rf "$target/docs/$docs"
  cp -R "$REPO_ROOT/docs/$docs" "$target/docs/$docs"

  # --- Root files ---
  cp "$REPO_ROOT/LICENSE" "$target/LICENSE"
  cp "$REPO_ROOT/.gitignore" "$target/.gitignore"

  # Adapt README: remove ../../ cross-refs
  sed -e 's|\.\./\.\./INSTALL\.md|INSTALL.md|g' \
      -e 's|\.\./\.\./README\.md|README.md|g' \
      "$REPO_ROOT/skills/$skill/README.md" > "$target/README.md"

  # Generate standalone INSTALL.md
  cat > "$target/INSTALL.md" <<EOF
# Installation — $repo_name

## Claude Code

\`\`\`bash
git clone https://github.com/$GITHUB_USER/$repo_name.git
mkdir -p ~/.claude/skills
cp -R $repo_name ~/.claude/skills/$skill
\`\`\`

Restart Claude Code — the skill auto-triggers on relevant prompts.

## Codex / Cursor / other AI agents

This repo follows the [agents.md](https://agents.md) spec. Most agents auto-read \`SKILL.md\` or \`AGENTS.md\` on project load. Alternatively, paste \`SKILL.md\` into your agent's rules / system prompt.

## API keys

\`\`\`bash
cp .env.example .env
# fill in your keys, then:
set -a; source .env; set +a
\`\`\`

## Run the Python examples directly

\`\`\`bash
pip install aiohttp httpx
python references/examples/<example>.py --help
\`\`\`

## Part of [\`crypto-claude-skills\`](https://github.com/$GITHUB_USER/crypto-claude-skills)

This skill is also included in the umbrella [\`crypto-claude-skills\`](https://github.com/$GITHUB_USER/crypto-claude-skills) collection alongside \`dune-skill\`, \`solscan-skill\`, \`nansen-skill\`, and \`solana-rpc-skill\`.
EOF

  write_env_example "$skill" "$target"

  # Generate standalone AGENTS.md
  cat > "$target/AGENTS.md" <<EOF
# AGENTS.md

> Instructions for AI coding agents. Follows the [agents.md](https://agents.md) spec.

This repository provides a Claude Code skill for **$skill** (see \`SKILL.md\`), packaged standalone. Content works with any AI agent — Claude Code auto-triggers it; Codex / Cursor / Windsurf / OpenCode read \`SKILL.md\` or this file as rules.

## Operating rules

1. **Credits are real money.** Respect budget thresholds documented in \`references/credits.md\` (where present). Announce estimated cost before expensive calls; stop at hard caps without explicit user approval.
2. **Scripts for batches, direct calls for exploration.** Over ~10 API calls of similar shape → write an async Python script with \`asyncio.Semaphore\`, resume-safe JSONL output, and rate-limit header monitoring. Templates in \`references/examples/\`.
3. **Prefer batch / parsed / enhanced endpoints** where the provider offers them (documented in each reference file).
4. **Never hardcode API keys** — read from env vars listed in \`.env.example\`.

## Setup

See \`README.md\` and \`INSTALL.md\`. For Python examples: \`pip install aiohttp httpx\` and set the keys from \`.env.example\`.

## Part of a collection

This skill is one of four — see umbrella at https://github.com/$GITHUB_USER/crypto-claude-skills.

## License

MIT.
EOF

  # --- Commit ---
  cd "$target"
  git add -A
  if git diff --staged --quiet; then
    echo "  no changes"
    return 0
  fi

  local msg
  if [[ "$(git rev-list --count HEAD 2>/dev/null || echo 0)" == "0" ]]; then
    msg="feat: initial release"
  else
    msg="chore: sync from crypto-claude-skills umbrella"
  fi
  git commit -q -m "$msg

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

  # --- Create github repo if --init ---
  if [[ "$init" == "--init" ]]; then
    if gh repo view "$GITHUB_USER/$repo_name" >/dev/null 2>&1; then
      echo "  github repo already exists"
      git remote get-url origin >/dev/null 2>&1 || \
        git remote add origin "https://github.com/$GITHUB_USER/$repo_name.git"
    else
      gh repo create "$repo_name" \
        --public \
        --description "$desc" \
        --source . \
        --remote origin \
        --push
      echo "  ✓ created https://github.com/$GITHUB_USER/$repo_name"
      return 0
    fi
  fi

  git push -q origin main
  echo "  ✓ pushed to https://github.com/$GITHUB_USER/$repo_name"
}

# --- Main ---
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <skill> [--init]"
  echo "       $0 --all [--init]"
  echo ""
  echo "Skills: dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles"
  exit 1
fi

if [[ "$1" == "--all" ]]; then
  init="${2:-}"
  for skill in dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles; do
    sync_skill "$skill" "$init"
  done
else
  sync_skill "$1" "${2:-}"
fi

echo ""
echo "Done."
