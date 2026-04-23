# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-24

Initial release. Four skills packaged together.

### Added
- **dune** skill — Dune Analytics SQL with 500/700 credit budget gates, FREE/PAID key rotation, 20-tool MCP catalog, 5 reference documents (tables, SQL templates, optimization, credits, paid endpoints)
- **solscan** skill — Solscan Pro v2 API with Tier 2 limits (150M CU/mo, 1000 req/min), discrete page_size handling, synchronous CSV exports, 3 async Python examples
- **nansen** skill — 37-chain Smart Money / Profiler / TGM coverage, `premium_labels: true` cost-trap awareness, live credit balance monitoring, 3 Python examples
- **solana-rpc** skill — universal Solana JSON-RPC for Helius / QuickNode / any provider, Helius Enhanced Tx + DAS, QuickNode addons, JSON-RPC array batching, 3 Python examples
- `.env.example`, `README.md`, `INSTALL.md`, `CONTRIBUTING.md`, MIT `LICENSE`
- Per-provider documentation corpus in `docs/` (including saved `llms-full.txt` for Nansen and Helius)
