#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
MS_DIR="$REPO_DIR/MuseScore"

cd "$MS_DIR"

shopt -s nullglob
patches=("$SCRIPT_DIR"/[0-9]*.patch)

if [ ${#patches[@]} -eq 0 ]; then
    echo "No patches to apply."
    exit 0
fi

for p in "${patches[@]}"; do
    echo "Applying $(basename "$p")..."
    git apply "$p"
done
echo "All patches applied."
