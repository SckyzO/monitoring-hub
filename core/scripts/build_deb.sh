#!/bin/bash
# Build a DEB package in a Docker container
# Usage: build_deb.sh <build_dir> <output_dir> <arch> <docker_image>

set -euo pipefail

if [ $# -lt 4 ]; then
    echo "Usage: $0 <build_dir> <output_dir> <arch> <docker_image>"
    exit 1
fi

BUILD_DIR="$1"
OUTPUT_DIR="$2"
ARCH="$3"
DOCKER_IMAGE="$4"

if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: Build directory not found: $BUILD_DIR"
    exit 1
fi

if [ ! -d "$BUILD_DIR/debian" ]; then
    echo "Error: debian/ directory not found in $BUILD_DIR"
    exit 1
fi

echo "=== Building DEB package ==="
echo "Build dir: $BUILD_DIR"
echo "Output dir: $OUTPUT_DIR"
echo "Architecture: $ARCH"
echo "Docker image: $DOCKER_IMAGE"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get absolute paths
BUILD_DIR_ABS=$(readlink -f "$BUILD_DIR")
OUTPUT_DIR_ABS=$(readlink -f "$OUTPUT_DIR")

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the build in Docker container
docker run --rm \
    -v "$BUILD_DIR_ABS:/build:ro" \
    -v "$OUTPUT_DIR_ABS:/output:rw" \
    -v "$SCRIPT_DIR/deb_entrypoint.sh:/entrypoint.sh:ro" \
    -e "ARCH=$ARCH" \
    -e "GPG_PRIVATE_KEY=${GPG_PRIVATE_KEY:-}" \
    -e "GPG_PASSPHRASE=${GPG_PASSPHRASE:-}" \
    -e "GPG_KEY_ID=${GPG_KEY_ID:-}" \
    --platform "linux/${ARCH}" \
    "$DOCKER_IMAGE" \
    /bin/bash /entrypoint.sh

echo ""
echo "=== DEB package(s) built successfully ==="
ls -lh "$OUTPUT_DIR"/*.deb
