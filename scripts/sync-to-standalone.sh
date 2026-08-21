#!/usr/bin/env bash
# Backward-compatible wrapper for the safe mirror sync tool.
# Dry-run is the default. Use --apply to update local checkouts and --push to publish.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/sync_mirrors.py" "$@"
