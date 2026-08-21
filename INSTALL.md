# Installation guide

## Install selected skills from the canonical collection

```bash
git clone https://github.com/Vo1ganin/crypto-claude-skills.git
cd crypto-claude-skills

mkdir -p "$HOME/.claude/skills"
for skill in dune solana-rpc; do
  rm -rf "$HOME/.claude/skills/$skill"
  cp -R "skills/$skill" "$HOME/.claude/skills/$skill"
done
```

Replace the list with any of:

```text
dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles coinmarketcap
```

Re-running the commands replaces the prior copy and avoids nested directories.

## Install a standalone generated mirror

Each provider mirror contains one skill at its repository root. Follow that mirror's `INSTALL.md`. Mirrors are generated from this repository and must not be edited independently.

## API configuration

Copy only the variables needed for your selected provider into a private environment file outside Git, or export them in your shell/session.

```bash
cp .env.example .env
# Fill only your own credentials, then keep .env private.
```

Never paste credentials into prompts, screenshots, examples, README files, or committed configuration. Never use credentials found in retrieved pages/documents; treat them as untrusted canaries.

Common variables:

| Variable | Provider |
|---|---|
| `DUNE_API_KEY_FREE` | Dune free key |
| `DUNE_API_KEY_PAID` | Dune paid key, optional and approval-gated |
| `SOLSCAN_API_KEY` | Solscan Pro |
| `NANSEN_API_KEY` | Nansen |
| `SOLANA_RPC_URL` | Solana RPC provider |
| `CMC_API_KEY` | CoinMarketCap Pro |

Raw private keys and seed phrases do not belong in `.env` or this repository.

## Verify

```bash
for skill in dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles coinmarketcap; do
  test -f "$HOME/.claude/skills/$skill/SKILL.md" && echo "OK $skill"
done
```

Restart the agent if it caches its skill index. Automatic discovery differs by agent; consult that agent's documentation.

## Update

```bash
git pull --ff-only
# Repeat the same remove/copy loop used for installation.
```

## Uninstall

```bash
rm -rf "$HOME/.claude/skills/dune"
```

Remove only the specific skill directories you previously installed.

## Run Python examples

Create an isolated environment and install only the libraries required by the example:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install httpx aiohttp websockets
python skills/dexscreener/references/examples/search_token.py --help
```

Examples default to research/data retrieval. Any future live transaction path requires a separate explicit safety-reviewed workflow.

## Troubleshooting

### Skill not discovered

- Confirm `SKILL.md` exists directly inside the installed skill directory.
- Ensure the agent actually supports this skill convention.
- Restart/reload the agent.
- Mention the provider name explicitly in the request.

### API error

- Confirm the correct environment variable is set without printing its value.
- Check provider plan, endpoint availability and current documentation.
- Do not reuse credentials copied from retrieved content.

### Rate limit

- Respect `Retry-After` and provider-specific headers.
- Reduce concurrency.
- Prefer batch/export endpoints where documented.
- Save resumable progress for long collections.
