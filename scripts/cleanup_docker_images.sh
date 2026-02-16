#!/usr/bin/env bash
set -euo pipefail

echo "🗑️  Cleaning up Docker images from GHCR..."
echo ""

# Get all Docker packages
packages=$(gh api 'user/packages?package_type=container' --jq '.[].name' | grep "monitoring-hub/" || true)

if [ -z "$packages" ]; then
    echo "✓ No Docker packages found"
    exit 0
fi

total=$(echo "$packages" | wc -l)
echo "Found $total Docker packages to delete"
echo ""

count=0
for package in $packages; do
    count=$((count + 1))
    # Extract just the exporter name
    exporter=$(echo "$package" | cut -d'/' -f2)
    echo "[$count/$total] Deleting package: $package"

    # Delete package (need to get package details first to get the package ID)
    package_type="container"

    if gh api -X DELETE "user/packages/$package_type/monitoring-hub%2F$exporter" 2>/dev/null; then
        echo "  ✓ Deleted"
    else
        echo "  ⚠️  Failed (may require manual deletion or different permissions)"
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Remaining packages:"
gh api 'user/packages?package_type=container' --jq '.[].name' | grep "monitoring-hub/" | wc -l || echo "  0"
