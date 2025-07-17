#!/usr/bin/env bash
# AutoSwingUS-Pro patch applier
# Usage: scripts/asw-apply-patch.sh <patch-file> [branch-name] [commit-msg]
#
# Reads a patch file that contains one or more blocks:
#   *** Begin Patch
#   *** Update File: path/to/file.py
#   @@
#   -old
#   +new
#   *** End Patch
#
# or *** Add File: ... for new files.
#
# For each block we write a temporary unified diff and feed it to `git apply`.
# We use --unidiff-zero so minimal context diffs work (what ChatGPT & Gemini produce).
#
set -euo pipefail

usage() {
  echo "Usage: $0 <patch-file> [branch-name] [commit-msg]" >&2
  exit 1
}

[[ $# -ge 1 ]] || usage
PATCH_FILE="$1"; shift || true
TARGET_BRANCH="${1:-}" || true
COMMIT_MSG="${2:-"Apply assistant patch"}"

if [[ ! -f "$PATCH_FILE" ]]; then
  echo "[ERR] patch file missing: $PATCH_FILE" >&2
  exit 1
fi

# Ensure we are in repo root
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
cd "$PROJECT_ROOT"

# If branch name provided, create/checkout from origin/main
if [[ -n "$TARGET_BRANCH" ]]; then
  git fetch origin main >/dev/null 2>&1 || true
  if git rev-parse --verify "$TARGET_BRANCH" >/dev/null 2>&1; then
    git checkout "$TARGET_BRANCH"
  else
    git checkout -b "$TARGET_BRANCH" origin/main || git checkout -b "$TARGET_BRANCH"
  fi
fi

TMPDIR="$(mktemp -d -t aswpatch.XXXXXX)"
trap 'rm -rf "$TMPDIR"' EXIT

curfile=""
blockfile=""
status=0

# read patch file line by line
while IFS='' read -r line || [[ -n "$line" ]]; do
  case "$line" in
    '*** Begin Patch'*)
      curfile=""; blockfile="";;
    '*** Update File:'*|'*** Add File:'*)
      # extract path after colon
      curfile="${line#*: }"
      # trim leading/trailing ws
      curfile="$(echo "$curfile" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      blockfile="$TMPDIR/$(echo "$curfile" | tr '/' '_').diff"
      # start diff header
      {
        echo "diff --git a/$curfile b/$curfile"
        echo "--- a/$curfile"
        echo "+++ b/$curfile"
      } >"$blockfile"
      ;;
    '*** End Patch'*)
      if [[ -n "$blockfile" && -s "$blockfile" ]]; then
        echo "[asw] applying $curfile"
        if ! git apply --unidiff-zero --apply "$blockfile"; then
          echo "[ERR] git apply failed for $curfile" >&2
          status=1
          break
        fi
      fi
      curfile=""; blockfile="";;
    @@*)
      # hunk header already provided by patch—just pass thru
      [[ -n "$blockfile" ]] && echo "$line" >>"$blockfile"
      ;;
    *)
      # raw patch lines (-/+/ context) pass through
      [[ -n "$blockfile" ]] && echo "$line" >>"$blockfile"
      ;;
  esac
done <"$PATCH_FILE"

if [[ $status -ne 0 ]]; then
  echo "[asw] patch aborted." >&2
  exit $status
fi

# Stage changes; if nothing changed exit quietly
if git diff --quiet; then
  echo "[asw] no changes detected (patch may already be applied)."
  exit 0
fi

git add -u
git add . 2>/dev/null || true

if git diff --cached --quiet; then
  echo "[asw] nothing staged; exiting."
  exit 0
fi

git commit -m "$COMMIT_MSG" || true

if [[ -n "$TARGET_BRANCH" ]]; then
  git push -u origin "$TARGET_BRANCH"
  echo "[asw] pushed branch '$TARGET_BRANCH'."
  echo "Open PR: https://github.com/$(git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)|(.git)##g')/compare/$TARGET_BRANCH?expand=1" || true
fi
