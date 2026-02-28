#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v git >/dev/null 2>&1; then
  echo "git is not available; skipping hook installation."
  exit 0
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git worktree; skipping hook installation."
  exit 0
fi

mkdir -p .githooks
chmod +x .githooks/pre-push
git config --local core.hooksPath .githooks

echo "Installed git hooks path: .githooks"
echo "Pre-push gate: .githooks/pre-push"

