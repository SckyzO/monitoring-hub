#!/bin/bash
set -euo pipefail

#
# Publish artifact metadata to gh-pages catalog
#
# This script:
# 1. Generates artifact JSON using generate_artifact_metadata.py
# 2. Commits it to gh-pages branch at catalog/<exporter>/<artifact>.json
#
# Usage:
#   ./publish_artifact_metadata.sh rpm node_exporter amd64 el9 release_urls.json
#   ./publish_artifact_metadata.sh deb redis_exporter amd64 ubuntu-22.04 release_urls.json
#   ./publish_artifact_metadata.sh docker mongodb_exporter "" "" docker_images.json
#

ARTIFACT_TYPE="$1"
EXPORTER="$2"
ARCH="${3:-}"
DIST="${4:-}"
RELEASE_URLS_FILE="$5"

# Validate inputs
if [ -z "$ARTIFACT_TYPE" ] || [ -z "$EXPORTER" ] || [ -z "$RELEASE_URLS_FILE" ]; then
    echo "Error: Missing required arguments"
    echo "Usage: $0 <type> <exporter> <arch> <dist> <release_urls_file>"
    exit 1
fi

if [ ! -f "$RELEASE_URLS_FILE" ]; then
    echo "Error: Release URLs file not found: $RELEASE_URLS_FILE"
    exit 1
fi

# Parse release_urls.json to extract package info
VERSION=$(jq -r '.tag | sub("^.*-v"; "")' "$RELEASE_URLS_FILE")
ASSETS=$(jq -c '.assets' "$RELEASE_URLS_FILE")

echo "============================================================"
echo "Publishing $ARTIFACT_TYPE metadata for $EXPORTER"
echo "Version: $VERSION"
echo "Arch: ${ARCH:-N/A}"
echo "Dist: ${DIST:-N/A}"
echo "============================================================"

# Determine output filename based on artifact type
if [ "$ARTIFACT_TYPE" = "docker" ]; then
    OUTPUT_FILENAME="docker.json"
else
    OUTPUT_FILENAME="${ARTIFACT_TYPE}_${ARCH}_${DIST}.json"
fi

CATALOG_DIR="catalog/$EXPORTER"
OUTPUT_FILE="$CATALOG_DIR/$OUTPUT_FILENAME"

# Create catalog directory
mkdir -p "$CATALOG_DIR"

# Extract first asset info (for RPM/DEB there should be only one per job)
if [ "$ARTIFACT_TYPE" != "docker" ]; then
    ASSET=$(echo "$ASSETS" | jq -c '.[0]')
    FILENAME=$(echo "$ASSET" | jq -r '.file')
    URL=$(echo "$ASSET" | jq -r '.url')

    # Download temporarily to get checksum and size
    echo "Downloading $FILENAME to extract metadata..."
    TEMP_FILE=$(mktemp)
    curl -sL "$URL" -o "$TEMP_FILE"

    SHA256=$(sha256sum "$TEMP_FILE" | awk '{print $1}')
    SIZE=$(stat -c%s "$TEMP_FILE")

    rm -f "$TEMP_FILE"

    echo "  SHA256: $SHA256"
    echo "  Size: $SIZE bytes"

    # Generate artifact metadata
    python3 core/scripts/generate_artifact_metadata.py \
        --type "$ARTIFACT_TYPE" \
        --exporter "$EXPORTER" \
        --version "$VERSION" \
        --arch "$ARCH" \
        --dist "$DIST" \
        --filename "$FILENAME" \
        --url "$URL" \
        --sha256 "$SHA256" \
        --size "$SIZE" \
        --status "success" \
        --output "$OUTPUT_FILE"
else
    # Docker: Parse images from release_urls (docker_images.json)
    DOCKER_IMAGES=$(jq -c '.images' "$RELEASE_URLS_FILE" 2>/dev/null || echo "[]")

    # Generate Docker metadata
    python3 core/scripts/generate_artifact_metadata.py \
        --type "docker" \
        --exporter "$EXPORTER" \
        --version "$VERSION" \
        --status "success" \
        --docker-images "$DOCKER_IMAGES" \
        --output "$OUTPUT_FILE"
fi

echo "✓ Artifact metadata generated: $OUTPUT_FILE"

# Commit to gh-pages (if in GitHub Actions)
if [ "${GITHUB_ACTIONS:-false}" = "true" ]; then
    echo ""
    echo "📤 Committing to gh-pages..."

    # Setup gh-pages worktree if not exists
    if [ ! -d "gh-pages-dist" ]; then
        git fetch origin gh-pages || git checkout --orphan gh-pages
        git worktree add -B gh-pages gh-pages-dist origin/gh-pages || \
            git worktree add --orphan gh-pages gh-pages-dist
    fi

    # Copy artifact JSON to gh-pages
    mkdir -p "gh-pages-dist/$CATALOG_DIR"
    cp "$OUTPUT_FILE" "gh-pages-dist/$OUTPUT_FILE"

    cd gh-pages-dist

    git config user.name "Monitoring Hub Bot"
    git config user.email "bot@monitoring-hub.local"

    git add "$OUTPUT_FILE"

    if git diff --staged --quiet; then
        echo "ℹ️  No changes to commit"
    else
        git commit -m "feat: add $OUTPUT_FILENAME for $EXPORTER v$VERSION

Artifact type: $ARTIFACT_TYPE
Architecture: ${ARCH:-N/A}
Distribution: ${DIST:-N/A}
Status: success"

        # Push with retry
        MAX_RETRIES=3
        RETRY_COUNT=0
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if git push origin gh-pages; then
                echo "✓ Successfully pushed to gh-pages"
                break
            else
                RETRY_COUNT=$((RETRY_COUNT + 1))
                if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                    echo "⚠️  Push failed, retrying ($RETRY_COUNT/$MAX_RETRIES)..."
                    git pull --rebase origin gh-pages
                else
                    echo "❌ Failed to push after $MAX_RETRIES attempts"
                    exit 1
                fi
            fi
        done
    fi

    cd ..

    echo "✓ Artifact metadata published to gh-pages"
else
    echo "ℹ️  Not in GitHub Actions, skipping gh-pages commit"
fi

echo ""
echo "============================================================"
echo "✅ Done: $OUTPUT_FILE"
echo "============================================================"
