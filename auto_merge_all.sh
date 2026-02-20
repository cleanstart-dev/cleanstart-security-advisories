#!/bin/bash

REPO="cleanstart-dev/cleanstart-security-advisories"
BASE_BRANCH="check"

echo "🚀 Fetching all open PRs requiring review..."

PRS=$(gh pr list \
  --repo $REPO \
  --search "is:open review:required" \
  --json number \
  --jq '.[].number')

if [ -z "$PRS" ]; then
  echo "✅ No PRs found requiring review."
else
  for pr in $PRS; do
    echo "🔎 Processing PR #$pr"

    echo "   ➜ Approving PR #$pr"
    gh pr review $pr --approve --repo $REPO

    echo "   ➜ Changing base to '$BASE_BRANCH'"
    gh pr edit $pr --repo $REPO --base $BASE_BRANCH
  done
fi

echo "🚀 Merging all PRs with base '$BASE_BRANCH'..."

MERGE_PRS=$(gh pr list \
  --repo $REPO \
  --base $BASE_BRANCH \
  --json number \
  --jq '.[].number')

if [ -z "$MERGE_PRS" ]; then
  echo "✅ No PRs found to merge."
else
  for pr in $MERGE_PRS; do
    echo "🔀 Merging PR #$pr"
    gh pr merge $pr --repo $REPO --merge --admin
  done
fi

echo "🎉 All done!"
