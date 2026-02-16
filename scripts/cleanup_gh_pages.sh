#!/usr/bin/env bash
set -euo pipefail

echo "🗑️  Cleaning up gh-pages branch..."
echo ""

# Create temporary directory for gh-pages
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

cd "$TEMP_DIR"

# Clone gh-pages branch
echo "📥 Cloning gh-pages branch..."
git clone --single-branch --branch gh-pages --depth 1 git@github.com:SckyzO/monitoring-hub.git .

# Configure git
git config user.name "Monitoring Hub Bot"
git config user.email "bot@monitoring-hub.local"

echo ""
echo "📂 Current structure:"
du -sh */ 2>/dev/null | sort -h || echo "  (empty)"
echo ""

# Keep only essential files
echo "🧹 Cleaning directories..."

# Remove all package repositories
rm -rf el8/ el9/ el10/ apt/ 2>/dev/null || true
echo "  ✓ Removed YUM/APT repositories"

# Remove old catalog
rm -rf catalog/ 2>/dev/null || true
echo "  ✓ Removed catalog"

# Keep index.html, README, GPG keys
# Remove everything else
find . -maxdepth 1 -type f ! -name 'index.html' ! -name 'README.md' ! -name '.gitignore' ! -name '*.asc' ! -name '*.gpg' -delete 2>/dev/null || true

# Recreate catalog structure
mkdir -p catalog
echo '{"version":"3.0","exporters":[]}' > catalog/index.json
echo "  ✓ Recreated empty catalog"

echo ""
echo "📂 New structure:"
du -sh */ 2>/dev/null | sort -h || echo "  (empty)"
echo ""

# Commit changes
git add -A
if git diff --staged --quiet; then
    echo "✓ Already clean, nothing to commit"
else
    git commit -m "chore: reset gh-pages for clean rebuild

- Remove all YUM/APT repositories
- Remove all catalog data
- Keep index.html and GPG keys
- Ready for fresh build with universal DEB architecture"

    echo "📤 Pushing to gh-pages..."
    git push origin gh-pages

    echo ""
    echo "✅ gh-pages cleaned successfully!"
fi
