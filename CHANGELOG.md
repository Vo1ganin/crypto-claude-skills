# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Eight-skill machine-readable manifest with neutral descriptions/topics.
- Deterministic standalone mirror builder and provenance files.
- Safe dry-run mirror sync tool and remote drift checker.
- CI for manifest, deterministic generation, Python syntax, safety, and scheduled public-mirror drift.

### Changed
- Reframed pump.fun and MEV skills around read-only research and monitoring.
- Removed public live transaction examples and raw-private-key environment guidance.
- Made the umbrella repository the sole canonical source; standalone repositories are generated mirrors.
- Updated installation and agent guidance for all eight skills.

### Security
- Propagated retrieved-credential/canary protections into generated mirror instructions.
- Added explicit read-only defaults and per-action approval boundary for future transaction workflows.

## [0.1.0] — 2026-04-24

Initial release. Four skills packaged together.

### Added
- **dune** skill — Dune Analytics SQL with 500/700 credit budget gates, FREE/PAID key rotation, 20-tool MCP catalog, 5 reference documents (tables, SQL templates, optimization, credits, paid endpoints)
- **solscan** skill — Solscan Pro v2 API with Tier 2 limits (150M CU/mo, 1000 req/min), discrete page_size handling, synchronous CSV exports, 3 async Python examples
- **nansen** skill — 37-chain Smart Money / Profiler / TGM coverage, `premium_labels: true` cost-trap awareness, live credit balance monitoring, 3 Python examples
- **solana-rpc** skill — universal Solana JSON-RPC for Helius / QuickNode / any provider, Helius Enhanced Tx + DAS, QuickNode addons, JSON-RPC array batching, 3 Python examples
- `.env.example`, `README.md`, `INSTALL.md`, `CONTRIBUTING.md`, MIT `LICENSE`
- Per-provider documentation corpus in `docs/` (including saved `llms-full.txt` for Nansen and Helius)
