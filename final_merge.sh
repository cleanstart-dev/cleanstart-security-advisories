#!/bin/bash

REPO="cleanstart-dev/cleanstart-security-advisories"
BASE="check"

echo "📥 Fetching PR list..."

gh pr list \
  --repo $REPO \
  --base $BASE \
  --json number,headRefName \
  --jq '.[] | "\(.number)|\(.headRefName)"' | while IFS="|" read PR_NUMBER BRANCH
do

  echo "-------------------------------------"
  echo "🔎 Processing PR #$PR_NUMBER"
  echo "🌿 Branch: $BRANCH"

  # Checkout PR
  gh pr checkout $PR_NUMBER --repo $REPO || continue

  # Update base
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

echo "🎉 All Done"
