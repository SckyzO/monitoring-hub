#!/bin/bash
set -e

SPEC_FILE=$1
OUTPUT_DIR=$2

if [ -z "$SPEC_FILE" ]; then
    echo "Usage: $0 <spec_file> <output_dir>"
    exit 1
fi

# Setup RPM build tree
rpmdev-setuptree

# Copy spec file to SPECS
cp "$SPEC_FILE" ~/rpmbuild/SPECS/

# Copy all files from spec dir to SOURCES (including the pre-extracted binary and config files)
SPEC_DIR=$(dirname "$SPEC_FILE")
cp -v "$SPEC_DIR"/* ~/rpmbuild/SOURCES/ || true

# Extract architecture from spec file to support cross-building (repack)
TARGET_ARCH=$(grep "BuildArch:" "$SPEC_FILE" | awk '{print $2}')
if [ -z "$TARGET_ARCH" ]; then
    TARGET_ARCH="x86_64"
fi

# Install build dependencies
echo "Installing build dependencies..."
dnf builddep -y ~/rpmbuild/SPECS/$(basename "$SPEC_FILE")

# Build RPM
echo "Building RPM for target: $TARGET_ARCH..."
rpmbuild -bb --target "$TARGET_ARCH" ~/rpmbuild/SPECS/$(basename "$SPEC_FILE")

# Copy artifacts to output
echo "Copying artifacts..."
cp -r ~/rpmbuild/RPMS/* "$OUTPUT_DIR/"

echo "Build complete."
ls -R "$OUTPUT_DIR"
