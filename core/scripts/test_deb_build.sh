#!/bin/bash
# Test script for building a DEB package locally in a container
# Usage: test_deb_build.sh [exporter] [dist] [arch]

set -euo pipefail

# Default values
EXPORTER="${1:-node_exporter}"
DIST="${2:-ubuntu-22.04}"
ARCH="${3:-amd64}"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== DEB Build Test ==="
echo "Exporter: $EXPORTER"
echo "Distribution: $DIST"
echo "Architecture: $ARCH"
echo ""

# Map distribution to Docker image
case "$DIST" in
    ubuntu-22.04)
        DOCKER_IMAGE="ubuntu:22.04"
        ;;
    ubuntu-24.04)
        DOCKER_IMAGE="ubuntu:24.04"
        ;;
    debian-12)
        DOCKER_IMAGE="debian:12"
        ;;
    debian-13)
        DOCKER_IMAGE="debian:trixie"
        ;;
    *)
        echo "Error: Unsupported distribution: $DIST"
        echo "Supported: ubuntu-22.04, ubuntu-24.04, debian-12, debian-13"
        exit 1
        ;;
esac

# Check if manifest exists
MANIFEST="${PROJECT_ROOT}/exporters/${EXPORTER}/manifest.yaml"
if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found: $MANIFEST"
    exit 1
fi

# Setup Python environment in container
echo "Step 1: Generating DEB packaging files..."
TEST_BUILD_DIR="${PROJECT_ROOT}/build/test_${EXPORTER}_${DIST}_${ARCH}"
mkdir -p "$TEST_BUILD_DIR"

docker run --rm \
    -v "$PROJECT_ROOT:/workspace:rw" \
    -w /workspace \
    python:3.11-slim \
    bash -c "
        pip install -q -r requirements/base.txt && \
        python3 -m core.engine.builder \
            --manifest exporters/${EXPORTER}/manifest.yaml \
            --arch ${ARCH} \
            --output-dir build/test_${EXPORTER}_${DIST}_${ARCH}
    "

# Check if debian/ directory was generated
if [ ! -d "$TEST_BUILD_DIR/debian" ]; then
    echo "Error: debian/ directory was not generated"
    echo "Make sure the manifest has deb.enabled: true"
    exit 1
fi

echo ""
echo "Step 2: Building DEB package in container..."
DEB_OUTPUT_DIR="${TEST_BUILD_DIR}/debs"
mkdir -p "$DEB_OUTPUT_DIR"

# Build the DEB package
"$SCRIPT_DIR/build_deb.sh" "$TEST_BUILD_DIR" "$DEB_OUTPUT_DIR" "$ARCH" "$DOCKER_IMAGE"

# Verify the built package
echo ""
echo "Step 3: Verifying DEB package..."
DEB_FILE=$(find "$DEB_OUTPUT_DIR" -name "*.deb" | head -1)

if [ -z "$DEB_FILE" ]; then
    echo "Error: No DEB file found in $DEB_OUTPUT_DIR"
    exit 1
fi

echo ""
echo "=== Package Information ==="
docker run --rm \
    -v "$DEB_OUTPUT_DIR:/debs:ro" \
    "$DOCKER_IMAGE" \
    bash -c "
        apt-get update -qq > /dev/null && \
        apt-get install -y -qq dpkg > /dev/null && \
        dpkg-deb --info /debs/$(basename "$DEB_FILE") && \
        echo '' && \
        echo '=== Package Contents ===' && \
        dpkg-deb --contents /debs/$(basename "$DEB_FILE")
    "

echo ""
echo "Step 4: Installing and testing package in container..."
docker run --rm \
    -v "$DEB_OUTPUT_DIR:/debs:ro" \
    "$DOCKER_IMAGE" \
    bash -c "
        apt-get update -qq > /dev/null && \
        apt-get install -y -qq /debs/$(basename "$DEB_FILE") && \
        echo '' && \
        echo '=== Installed Files ===' && \
        dpkg -L \$(dpkg-deb --field /debs/$(basename "$DEB_FILE") Package) && \
        echo '' && \
        echo '=== Binary Version ===' && \
        if [ -f /usr/bin/${EXPORTER} ]; then \
            /usr/bin/${EXPORTER} --version 2>&1 || true; \
        else \
            echo 'Binary not found at /usr/bin/${EXPORTER}'; \
        fi
    "

echo ""
echo "=== Test completed successfully ==="
echo "DEB file: $DEB_FILE"
echo "Build directory: $TEST_BUILD_DIR"
