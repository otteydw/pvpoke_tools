#!/bin/bash
set -e

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run this script as root."
  exit 1
fi

echo "🔧 Resolving merge conflicts..."

# 0️⃣ Handle files deleted by upstream but modified locally
deleted_by_them=$(git status | grep 'deleted by them' | awk '{print $4}')
if [ -n "$deleted_by_them" ]; then
  echo " → Removing files deleted by upstream:"
  echo "$deleted_by_them"
  echo "$deleted_by_them" | xargs -r git rm
fi

# 1️⃣ Always keep ours for formats.json
if git diff --name-only --diff-filter=U | grep -q 'src/data/gamemaster/formats.json'; then
  echo " → Keeping ours: src/data/gamemaster/formats.json"
  git checkout --ours -- src/data/gamemaster/formats.json
  git add src/data/gamemaster/formats.json
fi

# 2️⃣ Always keep theirs for gamemaster.min.json
if git diff --name-only --diff-filter=U | grep -q 'src/data/gamemaster.min.json'; then
  echo " → Keeping theirs: src/data/gamemaster.min.json"
  git checkout --theirs -- src/data/gamemaster.min.json
  git add src/data/gamemaster.min.json
fi

# 3️⃣ Always keep theirs for all rankings json files
conflicted_rankings=$(git diff --name-only --diff-filter=U | grep 'rankings-.*\.json' || true)
if [ -n "$conflicted_rankings" ]; then
  echo " → Keeping theirs for all ranking json files"
  echo "$conflicted_rankings" | xargs -r git checkout --theirs --
  echo "$conflicted_rankings" | xargs -r git add
fi

# 4️⃣ Backup and reset gamemaster.json to []
if git diff --name-only --diff-filter=U | grep -q 'src/data/gamemaster.json'; then
  timestamp=$(date +%Y-%m-%d-%H%M%S)
  backup_file="src/data/gamemaster.json.$timestamp.bak"
  echo " → Backing up gamemaster.json to $backup_file and resetting to []"
  mv src/data/gamemaster.json "$backup_file"
  echo "[]" >src/data/gamemaster.json
  git add src/data/gamemaster.json "$backup_file"
fi

# 5️⃣ Keep "theirs" for any other conflicts
other_conflicts=$(git diff --name-only --diff-filter=U)
if [ -n "$other_conflicts" ]; then
  echo " → Keeping theirs for remaining conflicted files:"
  echo "$other_conflicts"
  echo "$other_conflicts" | xargs -r git checkout --theirs --
  echo "$other_conflicts" | xargs -r git add
fi

# Add any other conflicted files that are not handled by the rules above
# and need to be staged. Check `git status` for unmerged paths.
git add -A

echo "✅ Merge conflicts resolved per rules."
