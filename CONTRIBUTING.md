# Contributing

Thanks for your interest! This project is a living collection of Claude Code skills for on-chain data APIs. The easiest way to help:

## Good first contributions

- **Report an outdated cost/limit** — providers change pricing. Open an issue with a screenshot and the file that needs updating.
- **Add an example script** — if you've written an async batch script for a common task (wallet labeling, NFT floor tracking, etc.), drop it in the relevant `skills/<skill>/references/examples/` folder.
- **Document an antipattern** — if you've made (or seen) an expensive mistake with any of these APIs, add it to `references/credits.md` or `references/patterns.md` of the affected skill. Real-world incidents save others money.

## Adding a new skill

Structure:

```
skills/<new-skill>/
├── SKILL.md                       ← frontmatter + workflow
└── references/
    ├── endpoints.md               ← API catalog
    ├── credits.md                 ← budget rules
    ├── patterns.md                ← batching / anti-patterns (optional)
    └── examples/*.py              ← at least one working script
```

`SKILL.md` must start with YAML frontmatter:

```yaml
---
name: <skill-name>
description: |
  When to trigger this skill. Be specific about keywords and use cases.
  Claude reads this to decide whether to invoke the skill.
compatibility:
  tools:
    - <MCP tool name>   # optional
    - Bash              # for direct HTTP
---
```

## Code style

- Python: stdlib + `aiohttp` / `httpx` only (no heavy deps)
- Scripts must read keys from env vars, never hardcode
- All examples must support **resume** (read existing output, skip done items)
- Always use `asyncio.Semaphore` for rate limiting
- Respect provider's `Retry-After` header on 429

## Commit convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(dune): add credit budget thresholds
fix(solscan): correct page_size allowed values for token/holders
docs(nansen): update pricing table for 2026
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
Scope: the skill name (`dune`, `solscan`, `nansen`, `solana-rpc`) or `repo` for cross-cutting changes.

## What NOT to commit

- `.env` files with real keys
- Script output (`*.jsonl`, `*.csv`, `data/`, `output/`)
- Anything under `docs/<provider>/` that wasn't in the official docs (we want reproducible sources)

## Reporting bugs

Issue template:

1. **Skill:** which one (`dune`, `solscan`, etc.)
2. **What happened:** minimal steps to reproduce
3. **Expected vs actual:** what the skill should have done
4. **Context:** any error messages, API responses

## Questions

Open an issue with the `question` label. PRs and discussions welcome.
