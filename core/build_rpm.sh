#!/bin/bash
set -e

# Usage: ./core/build_rpm.sh <path_to_spec_file> <output_dir>
# Example: ./core/build_rpm.sh build/node_exporter/node_exporter.spec build/node_exporter/rpms

SPEC_PATH=$(realpath "$1")
OUTPUT_DIR=$(realpath "$2")
SCRIPT_DIR=$(dirname "$(realpath "$0")")

mkdir -p "$OUTPUT_DIR"

echo "Starting RPM build for $SPEC_PATH..."
echo "Output directory: $OUTPUT_DIR"

# We map the project root to /workspace to access files
# We run as root in the container to allow dnf install
docker run --rm \
    -v "$(pwd):/workspace" \
    -v "$OUTPUT_DIR:/output" \
    -w /workspace \
    almalinux:9 \
    /bin/bash -c "dnf install -y rpmdevtools epel-release && \
                  dnf install -y 'dnf-command(builddep)' && \
                  /workspace/core/utils/rpm_build_entrypoint.sh '$SPEC_PATH' /output"

echo "RPM build finished."
