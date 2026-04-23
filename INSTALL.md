# Installation Guide

## Quick Install (single skill)

```bash
# 1. Clone this repo
git clone https://github.com/YOUR-USERNAME/crypto-claude-skills.git ~/crypto-skills
cd ~/crypto-skills

# 2. Copy the skill folder you want (e.g. dune)
cp -R skills/dune ~/.claude/skills/

# 3. Restart Claude Code
```

## Install all 4 skills

```bash
git clone https://github.com/YOUR-USERNAME/crypto-claude-skills.git ~/crypto-skills
cd ~/crypto-skills
for s in dune solscan nansen solana-rpc; do
  cp -R skills/$s ~/.claude/skills/
done
```

## Setup API keys

### Option A: .env file + source in shell

```bash
cd ~/crypto-skills
cp .env.example .env
# edit .env with your real keys
set -a; source .env; set +a
```

Python examples in `references/examples/` read from env vars (e.g. `SOLSCAN_API_KEY`, `NANSEN_API_KEY`, `SOLANA_RPC_URL`).

### Option B: Claude settings.json

For MCP-driven skills (Dune, Solscan), add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "dune": {
      "transport": { "type": "http", "url": "https://api.dune.com/mcp/v1" },
      "headers": { "x-dune-api-key": "YOUR_FREE_KEY" }
    },
    "solscan": {
      "command": "node",
      "args": ["/path/to/solscan-mcp/index.js"],
      "env": { "SOLSCAN_API_KEY": "YOUR_KEY" }
    }
  }
}
```

Skills use MCP tools when available and fall back to direct HTTP for advanced features.

## Verify

In Claude Code:
1. Type `/help` and check that skills list includes dune / solscan / nansen / solana-rpc
2. Ask: "What's the current Dune credit balance?" → skill should trigger and call `getUsage`
3. Ask: "Fetch defi activities for wallet X" (with any Solana wallet) → Solscan skill activates

## Uninstall

```bash
rm -rf ~/.claude/skills/{dune,solscan,nansen,solana-rpc}
```

## Troubleshooting

### "Skill not triggering"
- Check `~/.claude/skills/<skill>/SKILL.md` exists and starts with `---` frontmatter
- Restart Claude Code to refresh skill index
- Skills auto-trigger on description keywords — if your request is very abstract, mention the provider name explicitly

### "API key error"
- Verify env var is exported: `echo $SOLSCAN_API_KEY`
- Check correct header name (e.g. Nansen uses `apiKey` camelCase, Solscan uses `token`)

### "Rate limit 429"
- Each skill's `references/limits.md` has provider-specific guidance
- Drop semaphore in async scripts (typical safe values: Solscan 25, Nansen 15, Helius Business 15-20)
- Respect `Retry-After` header if present
