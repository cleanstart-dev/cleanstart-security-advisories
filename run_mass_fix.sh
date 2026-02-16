#!/bin/bash

prs=$(gh pr list --state open --json number,maintainerCanModify \
-q '.[] | select(.maintainerCanModify==true) | .number')

for pr in $prs; do
  echo "================================="
  echo "PR #$pr"
  echo "================================="

  gh pr checkout $pr

  python fix_osv_everywhere.py

  if [[ -n $(git status --porcelain) ]]; then
    git add .
    git commit -m "fix: normalize GHSA ids and advisory links"
    git push
    echo "✅ pushed"
  else
    echo "⏭ nothing to change"
  fi

  git checkout main
done
