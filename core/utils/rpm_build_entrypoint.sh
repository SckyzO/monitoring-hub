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

# Download sources
# spectool is part of rpmdevtools
echo "Downloading sources..."
spectool -g -R ~/rpmbuild/SPECS/$(basename "$SPEC_FILE")

# Install build dependencies
echo "Installing build dependencies..."
dnf builddep -y ~/rpmbuild/SPECS/$(basename "$SPEC_FILE")

# Build RPM
echo "Building RPM..."
rpmbuild -bb ~/rpmbuild/SPECS/$(basename "$SPEC_FILE")

# Copy artifacts to output
echo "Copying artifacts..."
cp -r ~/rpmbuild/RPMS/* "$OUTPUT_DIR/"

echo "Build complete."
ls -R "$OUTPUT_DIR"
