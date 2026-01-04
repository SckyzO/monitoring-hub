#!/bin/bash
set -e

# Usage: ./core/build_rpm.sh <path_to_spec_file> <output_dir>
# Example: ./core/build_rpm.sh build/node_exporter/node_exporter.spec build/node_exporter/rpms

SPEC_PATH_REL=$(realpath --relative-to="$(pwd)" "$1")
OUTPUT_DIR=$(realpath "$2")
TARGET_ARCH=${3:-amd64}
DOCKER_IMAGE=${4:-almalinux:9} # New argument for distribution image
SCRIPT_DIR=$(dirname "$(realpath "$0")")

mkdir -p "$OUTPUT_DIR"

echo "Starting RPM build for $SPEC_PATH_REL on arch $TARGET_ARCH using $DOCKER_IMAGE..."
echo "Output directory: $OUTPUT_DIR"

# Map arch names for Docker platform
if [ "$TARGET_ARCH" == "arm64" ] || [ "$TARGET_ARCH" == "aarch64" ]; then
    DOCKER_PLATFORM="linux/arm64"
else
    DOCKER_PLATFORM="linux/amd64"
fi

# We map the project root to /workspace to access files
# We run as root in the container to allow dnf install
# Note: We pass the path relative to /workspace inside the container
docker run --rm \
    --platform "$DOCKER_PLATFORM" \
    -v "$(pwd):/workspace" \
    -v "$OUTPUT_DIR:/output" \
    -w /workspace \
    "$DOCKER_IMAGE" \
    /bin/bash -c "dnf install -y rpmdevtools epel-release && \
                  dnf install -y 'dnf-command(builddep)' && \
                  /workspace/core/scripts/rpm_entrypoint.sh '/workspace/$SPEC_PATH_REL' /output"

echo "RPM build finished."
