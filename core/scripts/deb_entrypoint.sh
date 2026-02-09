#!/bin/bash
# Entrypoint script for building DEB packages inside Docker container
# This script is called by build_deb.sh

set -euo pipefail

echo "=== DEB Build Entrypoint ==="
echo "Architecture: ${ARCH}"
echo ""

# Install build dependencies
echo "Installing build dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
    build-essential \
    debhelper \
    devscripts \
    fakeroot \
    lintian \
    dpkg-dev \
    gnupg \
    > /dev/null

# Create build workspace
BUILD_WORKSPACE="/workspace"
mkdir -p "$BUILD_WORKSPACE"

# Copy source files to workspace (need write access for build)
echo "Copying source files to workspace..."
cp -r /build/* "$BUILD_WORKSPACE/"
cd "$BUILD_WORKSPACE"

# Ensure debian/rules is executable
chmod +x debian/rules

# Build the package (unsigned)
echo ""
echo "Building DEB package..."
dpkg-buildpackage -us -uc -b --host-arch="${ARCH}" 2>&1 | grep -v "dpkg-buildpackage: info:"

# Move built packages to output
echo ""
echo "Moving packages to output directory..."
mv ../*.deb /output/ 2>/dev/null || true
mv ../*.buildinfo /output/ 2>/dev/null || true
mv ../*.changes /output/ 2>/dev/null || true

# Fix permissions for output files
chmod 666 /output/* 2>/dev/null || true

# Sign packages if GPG key is provided
if [ -n "${GPG_PRIVATE_KEY:-}" ] && [ -n "${GPG_KEY_ID:-}" ]; then
    echo ""
    echo "Signing DEB packages with GPG..."

    # Create temporary GPG home
    GPG_HOME=$(mktemp -d)
    export GNUPGHOME="$GPG_HOME"
    chmod 700 "$GPG_HOME"

    # Import key
    echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --batch --import
    echo "${GPG_KEY_ID}:6:" | gpg --import-ownertrust

    # Sign each .deb file
    for deb in /output/*.deb; do
        if [ -f "$deb" ]; then
            echo "Signing: $(basename "$deb")"
            if [ -n "${GPG_PASSPHRASE:-}" ]; then
                echo "$GPG_PASSPHRASE" | gpg --batch --passphrase-fd 0 \
                    --detach-sign --armor -u "${GPG_KEY_ID}" "$deb"
            else
                gpg --batch --detach-sign --armor -u "${GPG_KEY_ID}" "$deb"
            fi
        fi
    done

    # Cleanup GPG home
    rm -rf "$GPG_HOME"

    echo "✓ Packages signed successfully"
fi

# List built packages
echo ""
echo "=== Built packages ==="
ls -lh /output/*.deb

# Run lintian checks (non-fatal)
echo ""
echo "=== Running lintian checks ==="
for deb in /output/*.deb; do
    if [ -f "$deb" ]; then
        echo "Checking: $(basename "$deb")"
        lintian --no-tag-display-limit "$deb" 2>&1 | head -20 || true
    fi
done

echo ""
echo "✓ Build completed successfully"
