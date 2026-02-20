#!/bin/bash

REPO="cleanstart-dev/cleanstart-security-advisories"
BASE="check"

echo "📥 Fetching PRs..."

PRS=$(gh pr list \
  --repo $REPO \
  --base $BASE \
  --json number,headRefName \
  --jq '.[] | "\(.number) \(.headRefName)"')

for item in $PRS; do
  PR_NUMBER=$(echo $item | awk '{print $1}')
  BRANCH=$(echo $item | awk '{print $2}')

  echo "🔎 Processing PR #$PR_NUMBER (branch: $BRANCH)"

  gh pr checkout $PR_NUMBER --repo $REPO

  git fetch origin
  git merge origin/$BASE --no-edit

  if [ $? -ne 0 ]; then
    echo "❌ Conflict in PR #$PR_NUMBER — skipping"
    git merge --abort
    continue
  fi

  git push

  echo "🔀 Merging PR #$PR_NUMBER"
  gh pr merge $PR_NUMBER --repo $REPO --merge --admin

done

echo "🎉 Done!"
