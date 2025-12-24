#!/bin/bash

# CRITICAL: Backdate Commits Script
# All commits after Dec 23, 2025 11:45 PM must be backdated

set -e

# Base date and time (Dec 23, 2025 9:00 PM)
BASE_DATE="2025-12-23 21:00:00"
BASE_TIMESTAMP=$(date -j -f "%Y-%m-%d %H:%M:%S" "$BASE_DATE" "+%s")

# Get list of commits after Dec 23, 2025 11:45 PM
CUTOFF_DATE="2025-12-23 23:45:00"
CUTOFF_TIMESTAMP=$(date -j -f "%Y-%m-%d %H:%M:%S" "$CUTOFF_DATE" "+%s")

echo "🔍 Checking for commits after Dec 23, 2025 11:45 PM..."
echo ""

# Get all commits on current branch
COMMITS=$(git log --format="%H %ct" --reverse)

# Track which commits need backdating
NEEDS_BACKDATE=()
COMMIT_TIMES=()

while IFS= read -r line; do
    HASH=$(echo "$line" | awk '{print $1}')
    TIMESTAMP=$(echo "$line" | awk '{print $2}')
    
    if [ "$TIMESTAMP" -gt "$CUTOFF_TIMESTAMP" ]; then
        NEEDS_BACKDATE+=("$HASH")
        COMMIT_TIMES+=("$TIMESTAMP")
    fi
done <<< "$COMMITS"

if [ ${#NEEDS_BACKDATE[@]} -eq 0 ]; then
    echo "✅ No commits found after cutoff date. All good!"
    exit 0
fi

echo "⚠️  Found ${#NEEDS_BACKDATE[@]} commit(s) that need backdating:"
echo ""

for i in "${!NEEDS_BACKDATE[@]}"; do
    HASH="${NEEDS_BACKDATE[$i]}"
    ORIGINAL_DATE=$(git log -1 --format="%ci" "$HASH")
    echo "  $((i+1)). ${HASH:0:8} - $ORIGINAL_DATE"
done

echo ""
echo "These will be backdated starting at: $BASE_DATE"
echo "Each commit will increment by 1 minute."
echo ""
read -p "Proceed with backdating? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
echo "🔄 Backdating commits..."
echo ""

# Backdate commits
for i in "${!NEEDS_BACKDATE[@]}"; do
    HASH="${NEEDS_BACKDATE[$i]}"
    
    # Calculate new timestamp (base + i minutes)
    NEW_TIMESTAMP=$((BASE_TIMESTAMP + (i * 60)))
    NEW_DATE=$(date -r "$NEW_TIMESTAMP" "+%Y-%m-%d %H:%M:%S")
    
    echo "  Backdating ${HASH:0:8} to $NEW_DATE..."
    
    # Use filter-branch to rewrite commit date
    GIT_COMMITTER_DATE="$NEW_DATE" git commit --amend --no-edit --date="$NEW_DATE" --allow-empty
done

echo ""
echo "✅ Backdating complete!"
echo ""
echo "⚠️  IMPORTANT: You now need to force push:"
echo "    git push --force-with-lease"
echo ""
