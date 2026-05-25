#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
MS_DIR="$REPO_DIR/MuseScore"

cd "$MS_DIR"

rm -f "$SCRIPT_DIR"/[0-9]*.patch

if git diff --quiet && git diff --cached --quiet; then
    echo "No modifications to MuseScore source."
    exit 0
fi

git diff > "$SCRIPT_DIR/0001-custom-changes.patch"
echo "Saved patch: $SCRIPT_DIR/0001-custom-changes.patch"
