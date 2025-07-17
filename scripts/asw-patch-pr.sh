#!/usr/bin/env bash
set -euo pipefail

PATCH_FILE="${1:-}"
BRANCH="${2:-asst-$(date +%Y%m%d-%H%M%S)}"
BASE="${3:-main}"

if [[ -z "$PATCH_FILE" || ! -f "$PATCH_FILE" ]]; then
  echo "[ERR] Patch file required and must exist." >&2
  exit 1
fi

TOKEN_FILE="${HOME}/.config/autoswing/gh_token"
if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "[ERR] GitHub token file not found: $TOKEN_FILE" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$TOKEN_FILE"
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "[ERR] GITHUB_TOKEN not set in $TOKEN_FILE" >&2
  exit 1
fi

REPO_OWNER="IBMaxin"
REPO_NAME="autoswingus_pro"
REMOTE_NAME="origin"

echo "[asw] Fetching latest from origin..."
git fetch "$REMOTE_NAME"

echo "[asw] Checking out base branch $BASE..."
git checkout "$BASE"
git pull "$REMOTE_NAME" "$BASE"

echo "[asw] Creating new branch: $BRANCH"
git checkout -b "$BRANCH"

echo "[asw] Applying patch: $PATCH_FILE"
git apply --whitespace=nowarn "$PATCH_FILE"

echo "[asw] Staging changes..."
git add -u
git add .

echo "[asw] Commit..."
git commit -m "Apply assistant patch: $PATCH_FILE"

AUTH_URL="https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"

echo "[asw] Pushing branch to GitHub..."
git push "$AUTH_URL" "$BRANCH"

PR_TITLE="Assistant patch: $PATCH_FILE"
PR_BODY="Automated patch applied via asw-patch-pr.sh"
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/pulls"

echo "[asw] Creating Pull Request..."
resp=$(curl -sSf -X POST \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "${API_URL}" \
  -d "$(jq -n --arg title "$PR_TITLE" --arg head "$REPO_OWNER:$BRANCH" --arg base "$BASE" --arg body "$PR_BODY" \
        '{title:$title, head:$head, base:$base, body:$body}')")

echo "$resp" | jq '.html_url // .message'
