#!/usr/bin/env bash
set -euo pipefail

echo "🗑️  Cleaning up all GitHub Releases..."
echo ""

# Get all release tags
tags=$(gh release list --limit 1000 --json tagName --jq '.[].tagName')

if [ -z "$tags" ]; then
    echo "✓ No releases found"
    exit 0
fi

total=$(echo "$tags" | wc -l)
echo "Found $total releases to delete"
echo ""

count=0
for tag in $tags; do
    count=$((count + 1))
    echo "[$count/$total] Deleting release: $tag"

    # Delete release and tag
    if gh release delete "$tag" --yes --cleanup-tag 2>/dev/null; then
        echo "  ✓ Deleted"
    else
        echo "  ⚠️  Failed (may already be deleted)"
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Remaining releases:"
gh release list --limit 10 || echo "  (none)"
