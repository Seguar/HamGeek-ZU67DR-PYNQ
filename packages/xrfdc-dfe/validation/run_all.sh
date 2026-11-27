#!/usr/bin/env bash
# Run from the coordinator, where the campaign lock is visible.
set -euo pipefail
dir=$(cd -- "$(dirname -- "$0")" && pwd)
exec python3 -B "$dir/launch.py" "$@"
