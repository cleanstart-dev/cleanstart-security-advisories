#!/bin/bash

REPO="cleanstart-dev/cleanstart-security-advisories"
BATCH=100

echo "Fetching open PRs from $REPO..."

while true; do
  PR_NUMBERS=$(gh pr list --repo "$REPO" --state open --limit $BATCH --json number --jq '.[].number')

  if [ -z "$PR_NUMBERS" ]; then
    echo "No more open PRs. Done."
    break
  fi

  COUNT=$(echo "$PR_NUMBERS" | wc -l)
  echo "Closing $COUNT PRs..."

  echo "$PR_NUMBERS" | xargs -P 10 -I {} gh pr close {} --repo "$REPO"

  echo "Batch done."
done
